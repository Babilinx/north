memory_size = 4096
variable_size = 512


def docol():
  global word_pointer
  if debug:
    print("- docol -")
    print(f"word_pointer = {word_pointer}")
  return_stack.append(word_pointer)
  word_pointer = int(colon_words[program_words[word_pointer]])

def colon():
  global word_pointer
  global program_words
  word_name = program_words[word_pointer+1]
  words[word_name] = docol
  colon_words[word_name] = word_pointer+1
  col_words = program_words[word_pointer+1:]
  while True:
    word_pointer += 1
    word = col_words[word_pointer]
    if word == ";":
      word_pointer += 1
      break

def semicolon():
  global word_pointer
  global return_stack
  if debug: print(f"return_stack = {return_stack}")
  word_pointer = int(return_stack.pop())

def store(data, ptr):
  global memory
  memory[ptr] = data

def variable():
  global word_pointer
  global program_words
  global variables
  global words
  global variable_stack_pointer
  word_pointer += 1
  variable_name = program_words[word_pointer]
  variable_ptr = variable_stack_pointer
  words[variable_name] = lambda: (variable_ptr,)
  variable_stack_pointer += 1

def constant(x):
  global word_pointer
  global program_words
  global constants
  global words
  word_pointer += 1
  constant_name = program_words[word_pointer]
  constants[constant_name] = x
  words[constant_name] = get_constant

def get_constant():
  global word_pointer
  global program_words
  global constants
  constant_name = program_words[word_pointer]
  return (constants[constant_name],)

def rpush(x):
  global return_stack
  return_stack.append(x)

def if_(x):
  global word_pointer
  global program_words
  global return_stack
  global data_stack
  global branch_stack
  global else_
  if_times = 1
  else_ = False
  return_stack.append(word_pointer)
  for word in program_words[word_pointer+1:]:
    if word == 'if':
      if_times += 1
    elif word == 'else' and if_times == 1:
      if debug: print(f"Found 'else' at {word_pointer}")
      branch_stack.append(word_pointer+1)
      else_ = True
    elif word == 'then':
      if_times -= 1
    if if_times == 0:
      branch_stack.append(word_pointer+1)
      break
    word_pointer += 1

  if debug:
    print(f"return_stack = {return_stack[-2:]}")
    print(f"branch_stack = {branch_stack[-1:]}")
    print("-- Condition ", "False" if debug and x != 0 else "", "True" if debug and x == 0 else "")
  # 0 is true
  if x != 0:
    # word_pointer is 'else' or 'then'
    if else_:
       branch_stack.pop()
    word_pointer = branch_stack.pop()
    return_stack.pop()
  else:
    # word_pointer is 'if'
    word_pointer = return_stack.pop()
    branch_stack[-1]

def else_():
  global word_pointer
  global branch_stack
  if debug: print(f"branch_stack = {branch_stack[-1:]}")
  word_pointer = branch_stack.pop()

def do():
  global word_pointer
  global program_words
  global loop_stack
  global return_stack
  return_stack.append(word_pointer)
  loop_stack.append(word_pointer)
  word_pointer += 1
  do_times = 1
  for word in program_words[word_pointer+1:]:
    if word == "do":
      do_times += 1
    elif word == "repeat":
      do_times -= 1
    elif word == "again":
      do_times -= 1
    elif word == "until":
      do_times -= 1
    if do_times == 0:
      # End of 'do' definition
      loop_stack.append(word_pointer+1)
      break
    word_pointer += 1

  if debug: print(f"loop_stack = {loop_stack}")
  word_pointer = return_stack.pop()

def leave():
  global word_pointer
  global loop_stack
  # End of do-loop address
  word_pointer = loop_stack.pop() + 1
  # 'do' address
  loop_stack.pop()

def while_(x):
  global word_pointer
  global loop_stack
  if x != 0:
    # 'repeat' address
    word_pointer = loop_stack.pop()
    # 'do' address
    loop_stack.pop()

def repeat():
  global word_pointer
  global loop_stack
  if debug: print(f"loop_stack = {loop_stack[-2]}")
  word_pointer = loop_stack[-2]

def again():
  global word_pointer
  global loop_stack
  if debug: print(f"loop_stack = {loop_stack[-2]}")
  word_pointer = loop_stack[-2]

def until(x):
  global word_pointer
  global loop_stack
  if x != 0:
    word_pointer = loop_stack[-2]
  else:
    word_pointer = loop_stack.pop()
    loop_stack.pop()

def source():
  global program_words
  global word_pointer
  word_pointer += 1
  filename = str(program_words[word_pointer])
  file = open(filename, 'r').read()
  program_words.extend(file.split())

def bye():
  global bye_
  bye_ = True

words = {
  '.': lambda x: print("-- Print " if debug else "", x, end="\n" if debug else " "),
  '.s': lambda: print("-- Print " if debug else "", f"<{len(data_stack)}> {data_stack}", end="\n" if debug else " "),
  'cr': lambda: print(),
  'dup': lambda x: (x, x),
  'drop': lambda x: (),
  'swap': lambda x, y: (y, x),
  'over': lambda y, x: (y, x, y),
  'rot': lambda z, y, x: (y, x, z),
  'nip': lambda y, x: (x,),
  'tuck': lambda y, x: (x, y, x),
  '+': lambda y, x: (y + x,),
  '-': lambda y, x: (y - x,),
  '*': lambda y, x: (y * x,),
  '/': lambda y, x: (y // x,),
  'mod': lambda y, x: (y % x,),
  'and': lambda y, x: (y & x,),
  'or': lambda y, x: (y | x,),
  'xor': lambda y, x: (y ^ x,),
  '<': lambda y, x: (0 if y < x else 1,),
  '>': lambda y, x: (0 if y > x else 1,),
  '<=': lambda y, x: (0 if y <= x else 1,),
  '>=': lambda y, x: (0 if y >= x else 1,),
  '!=': lambda y, x: (0 if y != x else 1,),
  '=': lambda y, x: (0 if y == x else 1,),
  ':': colon,
  ';': semicolon,
  '!': store,
  '@': lambda ptr: (memory[ptr],),
  'variable': variable,
  'constant': constant,
  '>r': rpush,
  'r>': lambda: (return_stack.pop(),),
  'r@': lambda: (return_stack[-1],),
  'true': lambda: (0,),
  'false': lambda: (1,),
  'if': if_,
  'else': else_,
  'then': (),
  'do': do,
  'leave': leave,
  'while': while_,
  'repeat': repeat,
  #'loop': loop,
  'until': until,
  'again': again,
  'source': source,
  'exit': lambda x: exit(x),
  'bye': bye,
}


def main():
  global return_stack
  global data_stack
  global branch_stack
  global loop_stack
  global program_words
  global word_pointer
  global colon_words
  global memory
  global variables
  global constants
  global variable_stack_pointer
  global bye_
  memory = [None for i in range(memory_size)]
  return_stack = []
  data_stack = []
  branch_stack = []
  loop_stack = []
  program_words = []
  word_pointer = 0
  colon_words = {}
  variables = {}
  constants = {}
  variable_stack_pointer = memory_size - variable_size - 1
  bye_ = False


  while not bye_:
    input_words = input("> ").split()
    print(f"\033[1A", *input_words, end=" ")
    program_words.extend(input_words)
    execute()
    print("ok")

def execute():
  global return_stack
  global data_stack
  global branch_stack
  global loop_stack
  global program_words
  global word_pointer
  global colon_words
  global memory
  global variables
  global constants
  global variable_stack_pointer

  if debug: print(f"len(program_words) = {len(program_words)}")

  while True:
    if word_pointer == len(program_words):
      return

    if debug: print(f"---- pointer = {word_pointer} ----")
    word = program_words[word_pointer]
    defined = True if word in words else False
    if debug: print(f"--- Word {word} ---")
    if not defined:
      if debug: print("Immediate")
      try:
        data_stack.append(int(word))
        word_pointer += 1
        continue
      except ValueError:
        print(f"Error: Immediate should be an integer, found '{word}'")
        exit(1)

    func = words[word]
    if callable(func):
      if debug: print(f"--- Func {func} ---")
      if debug: print("Callable")
      argindex = len(data_stack) - func.__code__.co_argcount
      if debug: print(f"argindex = {argindex}, type({type(argindex)})")
      args = data_stack[argindex:]
      if debug: print(f"args = {args}, type({type(args)})")
      del data_stack[argindex:]
      data_stack.extend(func(*args) or ())

    word_pointer += 1


if __name__ == '__main__':
  debug = True
  main()
