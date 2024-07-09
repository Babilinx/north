#!/usr/bin/env python3
import sys

memory_size = 4096

def docol():
  global program_words
  global colon_words
  global return_stack
  global word_pointer
  return_stack.append(word_pointer)
  word_pointer = colon_words[program_words[word_pointer]][0]

def colon():
  global word_pointer
  global program_words
  global colon_words
  global words
  # Next word is the word name
  word_pointer += 1
  word_name = program_words[word_pointer]
  # Skip comment fo faster word execution
  if program_words[word_pointer+1] == "(":
    for word in program_words[word_pointer:]:
      if word == ")": break
      word_pointer += 1
  # Save the last word address before word words
  colon_words[word_name] = [word_pointer, 0]
  # Define the new word as a colon word
  words[word_name] = docol
  for word in program_words[word_pointer:]:
    # Skip until end of colon definition
    if word == ";":
      colon_words[word_name][1] = word_pointer + 1
      break
    word_pointer += 1

def semicolon():
  global word_pointer
  global return_stack
  word_pointer = return_stack.pop()

def allot(x):
  global here
  here += x

def store(data, ptr):
  global memory
  memory[ptr] = data

def variable():
  global word_pointer
  global program_words
  global variables
  global words
  global here
  word_pointer += 1
  variable_name = program_words[word_pointer]
  variable_ptr = here
  words[variable_name] = lambda: (variable_ptr,)
  here += 1
  return (variable_ptr,)

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
      branch_stack.append(word_pointer+1)
      else_ = True
    elif word == 'then':
      if_times -= 1
    if if_times == 0:
      branch_stack.append(word_pointer+1)
      break
    word_pointer += 1

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
  word_pointer = branch_stack.pop()

def do():
  global word_pointer
  global program_words
  global data_stack
  global loop_stack
  global return_stack
  return_stack.append(word_pointer)
  loop_stack.append(word_pointer)
  word_pointer += 1
  do_times = 1
  for word in program_words[word_pointer+1:]:
    if word == "do":
      do_times += 1
    elif word in {"repeat", "again", "until", "loop"}:
      do_times -= 1
    if do_times == 0:
      '''
      At the end, loop_stack contain:
        [ start_address, *data, len(data), end_address ]
      '''
      # End of 'do' definition
      if word == "loop":
        # index = loop_stack[-3], limit = loop_stack[-4]
        loop_stack.extend((data_stack.pop(), data_stack.pop()))
        loop_stack.append(2)
      else:
        loop_stack.append(0)
      loop_stack.append(word_pointer+1)
      break
    word_pointer += 1

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
  if index < limit:
    word_pointer = loop_stack[-5]
    loop_stack[-4] = index
  else:
    leave()

def again():
  global word_pointer
  global loop_stack
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
  global word_pointer
  global error
  word_pointer += 1
  filename = str(program_words[word_pointer])
  try:
    file = open(filename, 'r').read().lower()
    program_words.extend(file.split())
  except FileNotFoundError:
    print(f"\nError: can't open file '{filename}'")
    error = True

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
  for word in program_words[word_pointer:]:
    if word == ")":
      comment_times -= 1
    elif word == "(":
      comment_times += 1
    if comment_times == 0:
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
  'until': until,
  'again': again,
  # I/O
  'source': source,
  '.': lambda x: print(x, end=" "),
  '.s': lambda: print(f"<{len(data_stack)}> {data_stack}", end=" "),
  'emit': lambda x: print(chr(int(x)), end=""),
  # Program flow
  'debug': lambda x: (),
  'exit': lambda x: exit(x),
  'bye': bye,
  'cleanup': cleanup_,
  # Comments
  '(': comment,
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
  global word_pointer
  global colon_words
  global memory
  global variables
  global constants
  global here
  global bye_
  global error
  global do_cleanup
  global program_words_len

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
  here = 0
  bye_ = False
  error = False
  do_cleanup = False

  try:
    program_words.extend(open("init.nth", "r").read().lower().split())
  except:
    print("INFO: 'init.nth' couldn't be loaded. Some words might be missing.")

  for arg in sys.argv[1:]:
    try:
      program_words.extend(open(arg, "r").read().lower().split())
    except:
      print(f"ERROR: '{arg}' couldn't be loaded!")
      exit(1)
  program_words_len = len(program_words)
  execute()
  if do_cleanup: cleanup()

  while not bye_:
    continue_ = False
    colon_def = False
    comment = False
    source = False
    input_words = input("> ")
    print(f"\033[1A", input_words, end=" ")
    new_words = input_words.lower().split()
    for word in new_words:
      if word == ":":
        colon_def = True
      elif word == "(":
        comment = True
      elif word == "source":
        source = True
      if not word in words and word.isdigit() and colon_def and comment and source:
        print(f"\nERROR: Undefined word '{word}'")
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
    program_words_len = len(program_words)
    execute()
    if not error:
      print("  ok")
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
  global word_pointer
  global colon_words
  global memory
  global variables
  global constants
  global here
  global error
  global program_words_len

  while True:
    if word_pointer == program_words_len:
      return

    word = program_words[word_pointer]
    defined = True if word in words else False
    if not defined:
      try:
        data_stack.append(int(word))
        word_pointer += 1
        continue
      # Undefined word
      except ValueError:
        print(f"\nError: Word '{word}' is undefined!")
        error = True
        word_pointer += 1
        continue

    func = words[word]
    argindex = len(data_stack) - func.__code__.co_argcount
    args = data_stack[argindex:]
    del data_stack[argindex:]
    data_stack.extend(func(*args) or ())

    word_pointer += 1


if __name__ == '__main__':
  main()
