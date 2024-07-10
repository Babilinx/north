#!/usr/bin/env python3
import sys
import cProfile
import pstats

memory_size = 4096

def docol():
  global program_words
  global colon_words
  global return_stack
  global word_pointer
  if debug:
    print("- docol -")
    print("word_pointer = {}".format(word_pointer))
    print("colon word address = {}".format(colon_words[program_words[word_pointer]][0]))
  return_stack.append(word_pointer)
  word_pointer = colon_words[program_words[word_pointer]][0]

def colon():
  global word_pointer
  global lower_program_words
  global colon_words
  global words
  global words_argc
  # Next word is the word name
  word_pointer += 1
  word_name = lower_program_words[word_pointer]
  # Skip comment fo faster word execution
  if lower_program_words[word_pointer+1] == "(":
    lower_next_words = lower_program_words[word_pointer:]
    for word in lower_next_words:
      if word == ")": break
      word_pointer += 1
  # Save the last word address before word words
  colon_words[word_name] = [word_pointer, 0]
  # Define the new word as a colon word
  words[word_name] = docol
  words_argc[word_name] = 0
  if debug: print("word_name = {}".format(word_name))
  lower_next_words = lower_program_words[word_pointer:]
  for word in lower_next_words:
    # Skip until end of colon definition
    if word == ";":
      colon_words[word_name][1] = word_pointer + 1
      break
    word_pointer += 1

def semicolon():
  global word_pointer
  global return_stack
  if debug:
    print("return_stack = {}".format(return_stack))
    print("- docol end -")
  word_pointer = return_stack.pop()

def allot(x):
  global here
  here += x

def store(data, ptr):
  global memory
  memory[ptr] = data

def variable():
  global word_pointer
  global lower_program_words
  global variables
  global words
  global words_argc
  global here
  word_pointer += 1
  variable_name = lower_program_words[word_pointer]
  variable_ptr = here
  words[variable_name] = lambda: (variable_ptr,)
  words_argc[variable_name] = 0
  here += 1
  return (variable_ptr,)

def constant(x):
  global word_pointer
  global program_words
  global constants
  global words
  global words_argc
  word_pointer += 1
  constant_name = program_words[word_pointer]
  constants[constant_name] = x
  words[constant_name] = get_constant
  words_argc[constant_name] = 0

def get_constant():
  global word_pointer
  global program_words
  global constants
  constant_name = program_words[word_pointer]
  return (constants[constant_name],)

def dot_quote():
  global word_pointer
  global program_words
  word_pointer += 1
  string = ""
  was_space = True
  elements = " ".join(program_words[word_pointer:])
  for c in elements:
    if c == '"':
      break
    elif c == " " and not was_space:
      was_space = True
      word_pointer += 1
    else: was_space = False
    string += c
  if debug: print("End of string = {}".format(word_pointer))
  print(string, end=" ") 

def start_string():
  global word_pointer
  global program_words
  global memory
  global here
  word_pointer += 1
  string = ""
  was_space = True
  elements = " ".join(program_words[word_pointer:])
  for c in elements:
    if c == '"':
      break
    elif c == " " and not was_space:
      was_space = True
      word_pointer += 1
    else: was_space = False
    string += c
  if debug: print("End of string = {}".format(word_pointer))
  string_ptr = here
  here += 1
  memory[string_ptr] = string
  return (string_ptr,)

def rpush(x):
  global return_stack
  return_stack.append(x)

def if_(x):
  global word_pointer
  global lower_program_words
  global return_stack
  global data_stack
  global branch_stack
  global else_
  if_times = 1
  else_ = False
  return_stack.append(word_pointer)
  lower_next_words = lower_program_words[word_pointer+1:]
  for word in lower_next_words:
    if word == 'if':
      if_times += 1
    elif word == 'else' and if_times == 1:
      if debug: print("Found 'else' at {}".format(word_pointer))
      branch_stack.append(word_pointer+1)
      else_ = True
    elif word == 'then':
      if_times -= 1
    if if_times == 0:
      branch_stack.append(word_pointer+1)
      break
    word_pointer += 1

  if debug:
    print("return_stack = {}".format(return_stack[-2:]))
    print("branch_stack = {}".format(branch_stack[-1:]))
    print("-- Condition ", "False" if debug and x != -1 else "", "True" if debug and x == -1 else "")
  # -1 is true
  if x != -1:
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
  if debug: print("branch_stack = {}".format(branch_stack[-1:]))
  word_pointer = branch_stack.pop()

def do():
  global word_pointer
  global lower_program_words
  global data_stack
  global loop_stack
  global return_stack
  return_stack.append(word_pointer)
  loop_stack.append(word_pointer)
  word_pointer += 1
  do_times = 1
  lower_next_words = lower_program_words[word_pointer+1:]
  for word in lower_next_words:
    word = word.lower()
    if word == "do":
      do_times += 1
    elif word in {"repeat", "again", "until", "loop", "+loop"}:
      do_times -= 1
    if do_times == 0:
      '''
      At the end, loop_stack contain:
        [ start_address, *data, len(data), end_address ]
      '''
      # End of 'do' definition
      if word in {"loop", "+loop"}:
        # index = loop_stack[-3], limit = loop_stack[-4]
        loop_stack.extend((data_stack.pop(), data_stack.pop()))
        loop_stack.append(2)
      else:
        loop_stack.append(0)
      loop_stack.append(word_pointer+1)
      break
    word_pointer += 1

  if debug: print("loop_stack = {}".format(loop_stack))
  word_pointer = return_stack.pop()

def leave():
  global word_pointer
  global loop_stack
  word_pointer = loop_stack[-1]
  elements_len = 3 + loop_stack[-2]
  # Remove the elements
  loop_stack = loop_stack[:len(loop_stack)-elements_len]

def while_(x):
  global word_pointer
  global loop_stack
  if x != -1:
    leave()

def repeat():
  global word_pointer
  global loop_stack
  word_pointer = loop_stack[-3]

def loop():
  global loop_stack
  global word_pointer
  limit = loop_stack[-3]
  index = loop_stack[-4] + 1
  if debug:
    print("loop_stack = {}".format(loop_stack))
    print("limit = {}".format(limit))
    print("index = {}".format(index))
  if index < limit:
    word_pointer = loop_stack[-5]
    loop_stack[-4] = index
  else:
    leave()

def plus_loop(x):
  global loop_stack
  global word_pointer
  limit = loop_stack[-3]
  index = loop_stack[-4] + x
  if index < limit:
    word_pointer = loop_stack[-5]
    loop_stack[-4] = index
  else:
    leave()

def again():
  global word_pointer
  global loop_stack
  if debug: print("loop_stack = {}".format(loop_stack[-3]))
  word_pointer = loop_stack[-3]

def until(x):
  global word_pointer
  global loop_stack
  if x != -1:
    word_pointer = loop_stack[-3]
  else:
    leave()

def source():
  global program_words
  global lower_program_words
  global word_pointer
  global error
  word_pointer += 1
  filename = str(program_words[word_pointer])
  try:
    file_words = open(filename, 'r').read().split()
    program_words.extend(file_words)
    lower_program_words.extend(file_words.lower())
  except FileNotFoundError:
    print("\nError: can't open file '{}'".format(filename))
    error = True

def debug_(x):
  global debug
  debug = True if x else False

def bye():
  global bye_
  bye_ = True

def cleanup_(x):
  global do_cleanup
  do_cleanup = True if x else False

def comment():
  global program_words
  global word_pointer
  comment_times = 1
  word_pointer += 1
  next_words = program_words[word_pointer:]
  for word in next_words:
    if word == ")":
      comment_times -= 1
    elif word == "(":
      comment_times += 1
    if comment_times == 0:
      if debug: print("comment_end = {}".format(word_pointer))
      break
    word_pointer += 1

words = {
  # Stack operations
  'dup': lambda x: (x, x),
  'drop': lambda x: (),
  'swap': lambda x, y: (y, x),
  'over': lambda y, x: (y, x, y),
  'rot': lambda z, y, x: (y, x, z),
  'nip': lambda y, x: (x,),
  'tuck': lambda y, x: (x, y, x),
  '>r': rpush,
  'r>': lambda: (return_stack.pop(),),
  'r@': lambda: (return_stack[-1],),
  # Arithmetic
  '+': lambda y, x: (y + x,),
  '-': lambda y, x: (y - x,),
  '*': lambda y, x: (y * x,),
  '/': lambda y, x: (y // x,),
  'mod': lambda y, x: (y % x,),
  # Logic
  'and': lambda y, x: (y & x,),
  'or': lambda y, x: (y | x,),
  'xor': lambda y, x: (y ^ x,),
  # Comparaison
  '<': lambda y, x: (-1 if y < x else 0,),
  '>': lambda y, x: (-1 if y > x else 0,),
  '<=': lambda y, x: (-1 if y <= x else 0,),
  '>=': lambda y, x: (-1 if y >= x else 0,),
  '!=': lambda y, x: (-1 if y != x else 0,),
  '=': lambda y, x: (-1 if y == x else 0,),
  # Word definition
  ':': colon,
  ';': semicolon,
  # Memory
  'here': lambda: (here,),
  'allot': allot,
  'cell': lambda: (1,),
  '!': store,
  '@': lambda ptr: (memory[ptr],),
  'variable': variable,
  'constant': constant,
  # Strings
  '."': dot_quote,
  's"': start_string,
  # Branching
  'i': lambda: (loop_stack[-4],),
  'if': if_,
  'else': else_,
  'then': lambda: (),
  'do': do,
  'leave': leave,
  'while': while_,
  'repeat': repeat,
  'loop': loop,
  '+loop': plus_loop,
  'until': until,
  'again': again,
  # I/O
  'source': source,
  '.': lambda x: print("-- Print " if debug else "", x, end="\n" if debug else " "),
  '.s': lambda: print("-- Print " if debug else "", "<{}> {}".format(len(data_stack), data_stack), end="\n" if debug else " "),
  'emit': lambda x: print(chr(int(x)), end=""),
  # Program flow
  'debug': debug_,
  'exit': lambda x: exit(x),
  'bye': bye,
  'cleanup': cleanup_,
  # Comments
  '(': comment,
}

words_argc = {
  # Stack operations
  'dup': 1,    'drop': 1,    'swap': 2,
  'over': 2,   'rot': 3,     'nip': 2,
  'tuck': 2,   '>r': 1,      'r>': 0,
  'r@': 0,
  # Arithmetic
  '+': 2,      '-': 2,       '*': 2,
  '/': 2,      'mod': 2,
  # Logic
  'and': 2,    'or': 2,      'xor': 2,
  # Comparaison
  '<': 2,      '>': 2,       '<=': 2,
  '>=': 2,     '!=': 2,      '=': 2,
  # Word definition
  ':': 0,      ';': 0,
  # Memory
  'here': 0,   'allot': 1,   'cell': 0,
  '!': 2,      '@': 1,       'variable': 0,
  'constant': 1,
  # Strings
  '."': 0,     's"': 0,
  # Branching
  'i': 0,      'if': 1,      'else': 0,
  'then': 0,   'do': 0,      'leave': 0,
  'while': 1,  'repeat': 0,  'loop': 0,
  '+loop': 1,  'until': 1,   'again': 0,
  # I/O
  'source': 0, '.': 1,       '.s': 0,
  'emit': 1,
  # Program flow
  'debug': 1,  'exit': 1,    'bye': 0,
  'cleanup': 1,
  # Comments
  '(': 0,
}


def cleanup():
  global program_words
  global word_pointer
  global program_words_len
  clean_program_words = []
  old_size = program_words_len
  for col_word, (start, end) in colon_words.items():
    #if debug: print(f"coldef: {program_words[start-1:end]}")
    clean_program_words.extend(program_words[start-1:end])
  #new_size = len(clean_program_words)
  program_words = clean_program_words
  # TODO: Refresh colon_words so we don't lose too much time
  word_pointer = 0
  #if debug: print(f"cleaned-up: {old_size} > {new_size}")


def main():
  global return_stack
  global data_stack
  global branch_stack
  global loop_stack
  global program_words
  global lower_program_words
  global word_pointer
  global colon_words
  global memory
  global variables
  global constants
  global here
  global bye_
  global error
  global do_cleanup
  global debug
  global program_words_len

  memory = [None for i in range(memory_size)]
  return_stack = []
  data_stack = []
  branch_stack = []
  loop_stack = []
  program_words = []
  lower_program_words = []
  word_pointer = 0
  colon_words = {}
  variables = {}
  constants = {}
  here = 0
  debug = False
  bye_ = False
  error = False
  do_cleanup = False

  try:
    init_words = open("init.nth", "r").read().split()
    program_words.extend(init_words)
    lower_program_words.extend([x.lower() for x in init_words])
  except:
    print("INFO: 'init.nth' couldn't be loaded. Some words might be missing.")

  if debug:
    print("### Args ###")
    print(sys.argv[1:])
  for arg in sys.argv[1:]:
    if arg in {"--profile", "-p"}:
      continue
    try:
      file_words = open(arg, "r").read().split()
      program_words.extend(file_words)
      lower_program_words.extend([x.lower() for x in file_words])
    except:
      print("ERROR: '{}' couldn't be loaded!".format(arg))
      exit(1)
  program_words_len = len(program_words)
  execute()
  if do_cleanup: cleanup()

  while not bye_:
    continue_ = False
    colon_def = False
    comment = False
    source = False
    input_ = input("> ")
    print("\033[1A", input_, end=" ")
    input_words = input_.split()
    new_words = input_words
    lower_new_words = [x.lower() for x in input_words]
    for word, lower_word in zip(new_words, lower_new_words):
      if word == ":":
        colon_def = True
      elif word == "(":
        comment = True
      elif lower_word == "source":
        source = True
      if not lower_word in words and word.isdigit() and colon_def and comment and source:
        print("\nERROR: Undefined word '{}'".format(word))
        continue_ = True
        break
      if word == ")":
        comment = False
      if colon_def:
        colon_def = False
      if source:
        source = False
    if continue_:
      continue
    program_words.extend(new_words)
    lower_program_words.extend([x.lower() for x in new_words])
    program_words_len = len(program_words)
    execute()
    if not error:
      print("  ok" if not debug else "-- OK")
    else: error = False

    if do_cleanup:
      # Only keep word definitions
      cleanup()


def execute():
  global return_stack
  global data_stack
  global branch_stack
  global loop_stack
  global program_words
  global lower_program_words
  global word_pointer
  global colon_words
  global memory
  global variables
  global constants
  global here
  global error
  global debug
  global program_words_len

  if debug: print("len(program_words) = {}".format(len(program_words)))

  while True:
    if word_pointer == program_words_len:
      return

    word = program_words[word_pointer]
    lower_word = lower_program_words[word_pointer]
    if debug:
      print("\n--- Word {} ---".format(word))
      print("---- pointer = {} ----".format(word_pointer))
    if not lower_word in words:
      if debug: print("Immediate")
      try:
        data_stack.append(int(word))
        word_pointer += 1
        continue
      # Undefined word
      except ValueError:
        print("\nError: Word '{}' is undefined!".format(lower_word))
        error = True
        word_pointer += 1
        continue

    func = words[lower_word]
    argc = words_argc[lower_word]
    argindex = len(data_stack) - argc
    if argindex < 0:
      print("\nStack underflow")
    args = data_stack[argindex:]
    if debug: 
      print("--- Func {} ---".format(func))
      print("Callable")
      print("argindex = {}".format(argindex))
      print("args = {}".format(args))
    del data_stack[argindex:]
    data_stack.extend(func(*args) or ())

    word_pointer += 1


if __name__ == '__main__':
  profile = False
  
  if "--profile" in sys.argv or "-p" in sys.argv:
    profile = True

  if profile:
    profiler = cProfile.Profile()
    profiler.enable()
  main()
  if profile:
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('tottime')
    stats.print_stats()
