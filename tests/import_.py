program = ''': cell 1 ;
: cells cell * ;
: buffer cells here swap allot ;

: true -1 ;
: false 0 ;

: 2dup over over ;
: 2drop drop drop ;

: 0= 0 = ;
: 0< 0 < ;
: 0> 0 > ;
 
: 1+ 1 + ;
: 1- 1 - ;

: invert if 0 else -1 then ;
: abs dup 0< if 0 swap - then ;

: cr 10 emit ;'''

def source():
  return program
