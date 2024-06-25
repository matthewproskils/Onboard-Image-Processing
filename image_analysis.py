import os


# Get Image File Size
def sortThroughDir(dir):
    # Maps through dir to return sorted list of touples of name and file size
    return sorted(
        list(
            map(
                lambda f: (
                    f,
                    os.stat(os.getcwd() +"/" + dir + "/" + f)[6],
                ),
                os.listdir(dir),
            )
        ),
        key=lambda x: x[1]
    )[::-1]


#   return sorted(
#     (
#         list(
#             map(
#                 lambda f: (f,   + '/' + dir + '/'  + f)[6]
#                 ),
#         os.listdir(dir))
#     ),
#     key=lambda x: x[1]
#   )

print(sortThroughDir("sd"))
