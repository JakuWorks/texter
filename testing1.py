import unicodedata
import pyperclip

categories_and_examples: dict[str, list[str]] = dict()
categories = set()
unassigned = set()
c1 = []

for i in range(0x10FFFF+1):
# for i in range(0xFFFF):
    char = chr(i)
    category = unicodedata.category(char)
    categories.add(category)
    if category == 'Cn':
       unassigned.add(char) 

for c in categories:
    categories_and_examples[c] = list()

for i in range(0x10FFFF+1):
    char = chr(i)
    category = unicodedata.category(char)
    list = categories_and_examples[category]
    list.append(char)

categories_and_examples['Cs'] = []
categories_and_examples['Cc'] = []
categories_and_examples['Cf'] = []
categories_and_examples['Mn'] = []
categories_and_examples['Mc'] = []


# with open("./sexer.txt", 'wt', encoding='utf-16') as f:
#     for c in categories_and_examples:
#         f.write(f"\n!!!!!{c}")
#         print(f"CATEGORY::: {c}")
#         for i in range(10):
#             try:
#                 char = categories_and_examples[c][i] 
#             except:
#                 continue
#             f.write('\n')
#             f.write(char)

with open("./sexer.txt", 'wt', encoding='utf-16') as f:
    for c in categories_and_examples:
        f.write(f"\n{c} ")
        print(f"CATEGORY::: {c}")
        for i in range(110):
            try:
                char = categories_and_examples[c][i] 
            except:
                continue
            f.write(char)

         
unassigned.add("!")

i = 0
for v in unassigned:
    c1.append(v)
    if i > 1999:
        break
    i = i+1

pyperclip.copy(''.join(c1))

# print(len(unassigned))
# print(categories)
# print(unassigned)