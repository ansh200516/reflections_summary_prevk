# 5-shot
standard_prompt = '''Use numbers and basic arithmetic operations (+ - * /) to obtain 24.
Input: 4 4 6 8
Answer: (4 + 8) * (6 - 4) = 24
Input: 2 9 10 12
Answer: 2 * 12 * (10 - 9) = 24
Input: 4 9 10 13
Answer: (13 - 9) * (10 - 4) = 24
Input: 1 4 8 8
Answer: (8 / 4 + 1) * 8 = 24
Input: 5 5 5 9
Answer: 5 + 5 + 5 + 9 = 24
Input: {input}
'''

# 5-shot
cot_prompt = '''Now just remember the tips from before (if any) and focus on the new task. Use numbers and basic arithmetic operations (+ - * /) to obtain 24. Each step, you are only allowed to choose two of the remaining numbers to obtain a new number.

Input: 4 4 6 8
Steps:
4 + 8 = 12 (left: 4 6 12)
6 - 4 = 2 (left: 2 12)
2 * 12 = 24 (left: 24)
Answer: (6 - 4) * (4 + 8) = 24
Input: 2 9 10 12
Steps:
12 * 2 = 24 (left: 9 10 24)
10 - 9 = 1 (left: 1 24)
24 * 1 = 24 (left: 24)
Answer: (12 * 2) * (10 - 9) = 24
Input: 4 9 10 13
Steps:
13 - 10 = 3 (left: 3 4 9)
9 - 3 = 6 (left: 4 6)
4 * 6 = 24 (left: 24)
Answer: 4 * (9 - (13 - 10)) = 24
Input: 1 4 8 8
Steps:
8 / 4 = 2 (left: 1 2 8)
1 + 2 = 3 (left: 3 8)
3 * 8 = 24 (left: 24)
Answer: (1 + 8 / 4) * 8 = 24
Input: 5 5 5 9
Steps:
5 + 5 = 10 (left: 5 9 10)
10 + 5 = 15 (left: 9 15)
15 + 9 = 24 (left: 24)
Answer: ((5 + 5) + 5) + 9 = 24
Input: {input}
Steps:
'''

cot_answer_prompt = '''You are an expert in the Game of 24. Your task is to output the final answer expression based on the provided input numbers and the sequence of steps that led to the solution. Your output must start with "Answer: ".

Input: 4 4 6 8
Steps:
4 + 8 = 12 (left: 4 6 12)
6 - 4 = 2 (left: 2 12)
2 * 12 = 24 (left: 24)
Answer: (6 - 4) * (4 + 8) = 24

Input: 2 9 10 12
Steps:
12 * 2 = 24 (left: 9 10 24)
10 - 9 = 1 (left: 1 24)
24 * 1 = 24 (left: 24)
Answer: (12 * 2) * (10 - 9) = 24

Input: {input}
Steps:
{steps}
'''

final_answer_prompt = '''You are an expert in the Game of 24. Your task is to extract the final answer expression from the provided input numbers and the sequence of steps that led to the solution. Your output must start with "Answer: " and contain nothing else, no need of writing any Note or clarifications.

Input: 4 4 6 8
Steps:
4 + 8 = 12 (left: 4 6 12)
6 - 4 = 2 (left: 2 12)
2 * 12 = 24 (left: 24)
Answer: (6 - 4) * (4 + 8) = 24

Your output:
Answer: (6 - 4) * (4 + 8) = 24

Input: 2 9 10 12
Steps:
12 * 2 = 24 (left: 9 10 24)
10 - 9 = 1 (left: 1 24)
24 * 1 = 24 (left: 24)
Answer: (12 * 2) * (10 - 9) = 24

Your output:
Answer: (12 * 2) * (10 - 9) = 24

Input: {input}
Steps:
{steps}

Your output:
'''

# 1-shot
propose_prompt = '''Now use numbers and basic arithmetic operations (+ - * /) to generate possible next steps. Make sure use steps that is sure to leads to 24 and avoid steps that are impossible to generate 24. Note that it is possible that we are considering intermediate steps so the numbers of the input may be less than 4.

Only output the possible next steps, do not output any other text, DON'T EXPLAIN ANYTHING, DON'T WRITE ANY NOTES, DON'T WRITE ANY COMMENTS, JUST OUTPUT THE POSSIBLE NEXT STEPS IN THE FORMAT BELOW.
Strictly follow the output format:
<number> <operation> <number> = <result> (left: <remaining_numbers>)
<number> <operation> <number> = <result> (left: <remaining_numbers>)
...

Example:
Input: 2 8 8 14 
2 + 8 = 10 (left: 8 10 14)
8 / 2 = 4 (left: 4 8 14)
14 + 2 = 16 (left: 8 8 16)
2 * 8 = 16 (left: 8 14 16)
8 - 2 = 6 (left: 6 8 14)
14 - 8 = 6 (left: 2 6 8)
14 /  2 = 7 (left: 7 8 8)
14 - 2 = 12 (left: 8 8 12)

Example:
Input: 2 5 8
5 - 2 = 3 (left: 3 8)
5 * 2 = 10 (left: 10 8)
8 / 2 = 4 (left: 4 5)

Input: {input}
'''

validation_prompt = '''Evaluate if given formula is a valid move in the game of 24. Especially, check if a number is missing, if the arithmetic is incorrect, or if a number is used that is not in the input or used twice.
Example

Input: 3 6 8 10
3 * 6 = 18 (left: 18 8 10)
valid

Input: 2 6 8 14
2 * 6 = 1 (left: 1 8 14)
invalid

Input: 4 6 8 10
10 * 5 = 50 (left: 6 50)
invalid

Input: 1 5 7
5 * 5 = 25 (left: 1 25 7)
invalid

Now evaluate the followng formula:
Input: {input}
{formula}
'''
# value_prompt = '''Now just remember the tips from before (if any) and focus on the new task. Evaluate if given numbers can reach 24 (sure/likely/impossible).
# 10 14
# 10 + 14 = 24
# sure
# 11 12
# 11 + 12 = 23
# 12 - 11 = 1
# 11 * 12 = 132
# 11 / 12 = 0.91
# impossible
# 4 4 10
# 4 + 4 + 10 = 8 + 10 = 18
# 4 * 10 - 4 = 40 - 4 = 36
# (10 - 4) * 4 = 6 * 4 = 24
# sure
# 4 9 11
# 9 + 11 + 4 = 20 + 4 = 24
# sure
# 5 7 8
# 5 + 7 + 8 = 12 + 8 = 20
# (8 - 5) * 7 = 3 * 7 = 21
# I cannot obtain 24 now, but numbers are within a reasonable range
# likely
# 5 6 6
# 5 + 6 + 6 = 17
# (6 - 5) * 6 = 1 * 6 = 6
# I cannot obtain 24 now, but numbers are within a reasonable range
# likely
# 10 10 11
# 10 + 10 + 11 = 31
# (11 - 10) * 10 = 10
# 10 10 10 are all too big
# impossible
# 1 3 3
# 1 * 3 * 3 = 9
# (1 + 3) * 3 = 12
# 1 3 3 are all too small
# impossible
# {input}
# '''

value_prompt  = '''
Evaluate if given numbers can reach 24 and choose labels from 'sure', 'likely' and 'impossible'. If the given numbers are already in the feedback above, just give the answer. Otherwise enumerate possible steps and try to give an approximate answer. Give the final answer in a separated line.
 {input}
 '''

value_prompt_2 = '''
Evaluate if given numbers can reach 24 and choose labels from 'sure', 'likely' and 'impossible'. If the given numbers are already in the feedback above, just give the answer. Otherwise enumerate possible steps and try to give an approximate answer.
10 14
10 + 14 = 24
sure
11 12
11 + 12 = 23
12 - 11 = 1
11 * 12 = 132
11 / 12 = 0.91
impossible
4 4 10
4 + 4 + 10 = 8 + 10 = 18
4 * 10 - 4 = 40 - 4 = 36
(10 - 4) * 4 = 6 * 4 = 24
sure
4 9 11
9 + 11 + 4 = 20 + 4 = 24
sure
5 7 8
5 + 7 + 8 = 12 + 8 = 20
(8 - 5) * 7 = 3 * 7 = 21
I cannot obtain 24 now, but numbers are within a reasonable range
likely
5 6 6
5 + 6 + 6 = 17
(6 - 5) * 6 = 1 * 6 = 6
I cannot obtain 24 now, but numbers are within a reasonable range
likely
10 10 11
10 + 10 + 11 = 31
(11 - 10) * 10 = 10
10 10 10 are all too big
impossible
1 3 3
1 * 3 * 3 = 9
(1 + 3) * 3 = 12
1 3 3 are all too small
impossible
{input}
'''

value_last_step_prompt = '''Use numbers and basic arithmetic operations (+ - * /) to obtain 24. Given an input and an answer, give a judgement (sure/impossible) if the answer is correct, i.e. it uses each input exactly once and no other numbers, and reach 24.
Input: 4 4 6 8
Answer: (4 + 8) * (6 - 4) = 24
Judge: 
sure
Input: 2 9 10 12
Answer: 2 * 12 * (10 - 9) = 24
Judge: 
sure
Input: 4 9 10 13
Answer: (13 - 9) * (10 - 4) = 24
Judge: 
sure
Input: 4 4 6 8
Answer: (4 + 8) * (6 - 4) + 1 = 25
Judge: 
impossible
Input: 2 9 10 12
Answer: 2 * (12 - 10) = 24
Judge: 
impossible
Input: 4 9 10 13
Answer: (13 - 4) * (10 - 9) = 24
Judge: 
impossible
Input: {input}
Answer: {answer}
Judge:'''

reflect_prompt = '''
Now we would like to play a game of 24. That is, given 4 numbers, try to use them with arithmetic operations (+ - * /) to get 24. Now we consider the following puzzle: {input}. 
Here is an attempt answer: 
{answer}
And we have the following feedback: 
{feedback}
Now using the above feedback, give 'sure' or 'impossible' labels for each formula with left numbers from each step. Give 'sure' if the formula is correct and can lead to 24 and give 'impossible' if the formula is incorrect or illegal. First repeat the formula with left numbers from each step above and then give the label, with the following form: {{formula}} (left: {{left numbers}}): {{label}}.
'''

value_reflect_prompt = '''
Now we would like to play a game of 24. That is, given 4 numbers, try to use them with arithmetic operations (+ - * /) to get 24. Now we consider the following puzzle: {input}. 
Here is an attempt answer:
{answer}
And we have the following feedback:
{feedback}
Now using the above feedback, give 'sure' or 'impossible' labels for left numbers from each step. Give 'sure' if the formula is correct and left numbers can lead to 24 and give 'impossible' if the formula is incorrect or illegal. First repeat the left numbers from each step above and then give the label, with the following form: {{left numbers}}: {{label}}.
'''
