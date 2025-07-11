import os
import re
import time
import asyncio
import logging
import argparse
import numpy as np
from diskcache import Cache
from openai import AsyncOpenAI
from omegaconf import OmegaConf
from together import AsyncTogether
from dotenv import load_dotenv
logger = logging.getLogger(__name__)


import sys
sys.path.append(os.getcwd())
from cachesaver.pipelines import OnlineAPI
from src.utils import tokens2cost, clean_log
from src.algorithms import *
from src.models import OnlineLLM, API
from src.typedefs import DecodingParameters
from src.tasks.scibench import *
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def build_method(method_name: str, params: DecodingParameters, api: API, config: OmegaConf):
# Setup the method
    if method_name == "foa":
        agents = AgentDictFOA(
            step=AgentActSciBench,
            evaluate=AgentEvaluateSciBench,
            step_params=params,
            eval_params=params,
        )
        method = AlgorithmFOA(
            model=api,
            agents=agents,
            env=EnvironmentSciBench,
            num_agents=config.foa.num_agents,
            num_steps=config.foa.num_steps,
            k=config.foa.k,
            backtrack=config.foa.backtrack,
            resampling=config.foa.resampling,
            origin=config.foa.origin,
            min_steps=config.foa.min_steps,
            num_evaluations=config.foa.num_evaluations,
        )
    elif method_name == "het_foa":
        step_agents = []

        # build the fleet of agents here
        step_agents.append({
            "agent": AgentValueReduceReflectSciBench,
            "params": params,
            "num_agents": config.het_foa.num_agents - config.het_foa.num_agents // 2,
        })

        step_agents.append({
            "agent": AgentReactSciBench,
            "params": params,
            "num_agents": config.het_foa.num_agents // 2,
        })

        agents = AgentDictHeterogenousFOA(
            evaluate=AgentEvaluateSciBench,
            eval_params=params,
            step_agents=step_agents
        )
        
        logger.info(f"Using these agents for Heterogenous FOA:")
        for i in range(len(agents["step_agents"])):
            logger.info(f"{step_agents[i]['agent'].__name__} ({agents['step_agents'][i]['num_agents']}): Temperature: {agents['step_agents'][i]['params'].temperature}, Top P: {agents['step_agents'][i]['params'].top_p}")

        method = AlgorithmHeterogenousFOA(
            model=api,
            agents=agents,
            env=EnvironmentSciBench,
            num_agents=config.het_foa.num_agents,
            num_steps=config.het_foa.num_steps,
            k=config.het_foa.k,
            backtrack=config.het_foa.backtrack,
            resampling=config.het_foa.resampling,
            origin=config.het_foa.origin,
            min_steps=config.het_foa.min_steps,
            num_evaluations=config.het_foa.num_evaluations,
        )
        
    elif method_name == "tot_bfs":
        agents = AgentDictTOT(
            step=AgentBfsSciBench,
            evaluate=AgentEvaluateSciBench,
            step_params=params,
            eval_params=params,
        )
        method = AlgorithmTOT(
            model=api,
            agents=agents,
            env=EnvironmentSciBench,
            num_selections=config.tot_bfs.num_selections,
            num_steps=config.tot_bfs.num_steps,
            num_evaluations=config.tot_bfs.num_evaluations,
        )
    elif method_name == "got":
        agents = AgentDictGOT(
            step=AgentActSciBench,
            aggregate=AgentAggregateSciBench,
            evaluate=AgentEvaluateSciBench,
            step_params=params,
            aggregate_params=params,
            eval_params=params,
        )
        method = AlgorithmGOT(
            model=api,
            agents=agents,
            env=EnvironmentSciBench,
            num_selections=config.got.num_selections,
            num_steps=config.got.num_steps,
            num_generate=config.got.num_generate,
            num_best=config.got.num_best,
            num_evaluations=config.got.num_evaluations,
        )
    elif method_name == "react":
        agents = AgentDictReact(
            step=AgentReactSciBench,
            step_params=params,
        )
        method = AlgorithmReact(
            model=api,
            agents=agents,
            env=EnvironmentSciBench,
            num_steps=config.react.num_steps,
        )
        
    elif method_name == "reflect_summary":
        agents = AgentDictReflectSummary(
            step=AgentReflectSummarySciBench,
            step_params=params,
            eval_params=params,
            evaluate=AgentEvaluateSciBench,
        )
        method = AlgorithmReflectSummary(
            model=api,
            agents=agents,
            env=EnvironmentSciBench,
            num_steps=config.reflect_summary.num_steps,
            num_evaluations=config.reflect_summary.num_evaluations,
            origin=config.reflect_summary.origin,
            min_steps=config.reflect_summary.min_steps,
        )
        
    elif method_name=="reflect_prev_k":
        agents=AgentDictReflectPrevK(
            step=AgentReflectPrevKSciBench,
            step_params=params,
            eval_params=params,
            evaluate=AgentEvaluateSciBench,
        )
        method=AlgorithmReflectPrevK(
            model=api,
            agents=agents,
            env=EnvironmentSciBench,
            num_steps=config.reflect_prev_k.num_steps,
            num_evaluations=config.reflect_prev_k.num_evaluations,
            origin=config.reflect_prev_k.origin,
            min_steps=config.reflect_prev_k.min_steps,
            k=config.reflect_prev_k.k,
        )

    else:
        raise NotImplementedError(f"Method {method_name} is not implemented yet.")
    return method

async def run(args, trial, cache_path):
    # Cache to be used
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    cache = Cache(cache_path)

    # LLM Provider
    if args.provider == "openai":
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    elif args.provider == "together":
        client = AsyncTogether()
    elif args.provider == "local":
        raise NotImplementedError("Local client is not implemented yet.")
    else:
        raise ValueError("Invalid provider. Choose 'openai', 'together', or 'local'.")
    
    # CacheSaver model layer
    if args.provider in ["openai", "together"]:
        model = OnlineLLM(client=client)
    else:
        raise NotImplementedError("Local model is not implemented yet.")
    
    # CacheSaver Pipeline: Batcher -> Reorderer -> Deduplicator -> Cache -> Model
    pipeline = OnlineAPI(
                    model=model,
                    cache=cache,
                    batch_size=args.batch_size,
                    timeout=args.timeout,
                    allow_batch_overflow=True,
                    correctness=bool(args.correctness)
                    )
    
    # Cachesaver additional layer for wrapping: API -> Pipeline
    api = API(
        pipeline=pipeline,
        model=args.model
    )

    # Decoding parameters
    params = DecodingParameters(
        temperature=args.temperature,
        max_completion_tokens=args.max_completion_tokens,
        top_p=args.top_p,
        stop=args.stop,
        logprobs=args.logprobs
    )

    # Config for framework hyperpaarameters
    config = OmegaConf.load(args.conf_path)

    # Build the method
    method = build_method(args.method, params, api, config)

    # Load the dataset
    benchmark = BenchmarkSciBench(path=args.dataset_path, split=args.split, task=args.task)

    # Run the method
    start = time.time()
    results = await method.benchmark(
        benchmark=benchmark,
        share_ns=True,
        cache=args.value_cache,
    )
    end = time.time()

    finished = []
    correct = []
    for result in results:
        evaluations = sorted([EnvironmentSciBench.evaluate(state) for state in result], key=lambda x: x[1])
        finished.append(False if len(evaluations) == 0 else evaluations[-1][0])
        correct.append(1.0 if len(evaluations) == 0 else evaluations[-1][1])
    perc_finished = sum(finished) / len(finished)
    perc_correct = sum(correct) / len(correct)
    costs = {key:tokens2cost(api.tokens[key], args.model)["total"] for key in api.tokens.keys()}
    latency = {
        "mean": np.mean(api.latencies), 
        "std": np.std(api.latencies),
        "max": np.max(api.latencies), 
        "min": np.min(api.latencies), 
        "total": np.sum(api.latencies)
        }
    reuse = {
        "mean": np.mean(list(api.reuse.values())),
        "std": np.std(list(api.reuse.values())),
        "max": np.max(list(api.reuse.values())),
        "min": np.min(list(api.reuse.values())),
        "median": np.median(list(api.reuse.values())),
        "total" : np.sum(list(api.reuse.values())),
        "num_unique": len(api.reuse),
    }
    run_time = end - start
    throughput = len(benchmark) / run_time

    logger.info(f"Finished: {perc_finished:.2f} (trial {trial})")
    logger.info(f"Correct: {perc_correct:.2f} (trial {trial})")
    logger.info(f"Costs: {costs} (trial {trial})")
    logger.info(f"Latency: {latency['mean']} (trial {trial})")
    logger.info(f"Run time: {run_time:.2f} seconds (trial {trial})")
    logger.info(f"Throughput: {throughput:.2f} puzzles/second (trial {trial})")

    logger.info(f"Correct (deailed): {correct} (trial {trial})")
    logger.info(f"Tokens (detailed): {api.tokens} (trial {trial})")
    logger.info(f"Calls (detailed): {api.calls} (trial {trial})")
    logger.info(f"Reuse (detailed): {reuse} (trial {trial})")
    
    print("All good.")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solve Game 24 using LLMs.")
    parser.add_argument("--provider", type=str,default="openai", help="LLM provider")
    parser.add_argument("--base_url", type=str,default=None, help="Base URL for the API")
    parser.add_argument("--model", type=str,default="gpt-4.1-nano", help="LLM model")
    parser.add_argument("--batch_size", type=int,default=15, help="CacheSaver's batch size")
    parser.add_argument("--timeout", type=float, default=1,help="CacheSaver's timeout")
    parser.add_argument("--temperature", type=float,default=0.7, help="Temperature for the model")
    parser.add_argument("--max_completion_tokens", type=int, help="Max completion tokens")
    parser.add_argument("--top_p", type=float,default=1, help="Top P for the model")
    parser.add_argument("--stop", type=str, nargs="+", help="Stop sequence for the model")
    parser.add_argument("--logprobs", action="store_true", help="Logprobs for the model")
    parser.add_argument("--dataset_path",default="./datasets/dataset_scibench.csv.gz" ,type=str, help="Path to the dataset")
    parser.add_argument("--split", type=str,default="single", help="Split of the dataset")
    parser.add_argument("--method", type=str,default="foa", help="Method to use")
    parser.add_argument("--conf_path", type=str, default="./scripts/frameworks/scibench/scibench.yaml",help="Path to corresponding config")
    parser.add_argument("--value_cache", action="store_true", help="Use value cache")
    parser.add_argument("--correctness", type=int, help="Use original ('correct') implementation")
    parser.add_argument("--task", type=str, help="Task to run", default="chemmc")
    args = parser.parse_args()

    filename = f"logs/correctness/{args.model.split('/')[-1]}/scibench_{args.task}/{args.method}.log"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    logging.basicConfig(level=logging.INFO, filename=filename, filemode="a")
    logger.info("#"*50)

    # Load previous content
    with open(filename, "r") as f:
        contents = f.read()
    
    if args.batch_size == 1:
        previous_trials = [int(num) for num in re.findall(r"Shared Namespace \(trial (\d+)\)", contents)]
        trial = max(previous_trials) + 1 if previous_trials else 1
        logger.info(f"Shared Namespace (trial {trial})")
        cache_path = f"caches/correctness/scibench/{args.method}/sns_{trial}"
    else:
        previous_trials = [int(num) for num in re.findall(r"Shared Namespace and Batch \(trial (\d+)\)", contents)]
        trial = max(previous_trials) + 1 if previous_trials else 1
        logger.info(f"Shared Namespace and Batch (trial {trial})")
        cache_path = f"caches/correctness/scibench/{args.method}/snsb_{trial}"

    asyncio.run(run(args, trial=trial, cache_path=cache_path))
    logger.info("\n"*3)
    clean_log(filename)
