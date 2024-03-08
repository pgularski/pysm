from test_simple_on_off import sm
import string

def test_plantuml():

    remove = string.whitespace
    mapping = {ord(c): None for c in remove}

    uml_expected = """
        @startuml
            sm:
        state sm {
            [*] --> on
            on --> off: off
            off --> on: on
        }
        @enduml
        """
    uml_expected = uml_expected.translate(mapping)
    uml = sm.to_plantuml().translate(mapping)

    assert uml == uml_expected