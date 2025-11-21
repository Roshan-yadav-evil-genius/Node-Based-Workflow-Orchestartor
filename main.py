from rich import print
from Node.Node import Node

if __name__ == "__main__":
    my_node = Node()
    print(my_node.schema())
    data = {"country": "India"}
    states = my_node.get_populated_field_value(data)
    print(states)
