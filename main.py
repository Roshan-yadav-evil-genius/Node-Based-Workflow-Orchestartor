from rich import print
from Nodes.PlaceNode import PlaceNode

if __name__ == "__main__":
    my_node = PlaceNode()
    print(my_node.form_schema())
    data = {"country": "India"}
    states = my_node.get_populated_field_value(data)
    print(states)
    my_node.populate_values(data)
    print(my_node.form_schema())

