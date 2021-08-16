


### finding an item in a list. change it to a set first
### This is because searching a large list will take more time than sreaching a set

list_of_letters = ["A", "B", "G", "D", "A", "B", "B"]

# anti pattern
check = "A" in list_of_letters

# good practice
check = "A" in set(list_of_letters)



### functions with mutable defaults
### this is because the default can be mutated for all future agruments

# anti pattern
def append_to(element, to=[]):
    to.append(element)
    return to

# good practice. this makes it clear that when calling the function again the default is reset to None
def append_to(element, to=None):
    if to is None:
        to = []
    to.append(element)
    return to



### Returning different types
### This makes the returned code inconsistent and the type intended is not the type returned. This can causes errors

# anti pattern
def get_code(username):
    if username != "admin":
        return "normal user"
    else:
        return None

code = get_code("bobus")

# good practice.
def get_code(username):
    if username != "admin":
        return "normal user"
    else:
        raise ValueError

try:
    code = get_code("bobus")
except:
    print("Wrong username")
