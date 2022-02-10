import pytest
import json
from automation_services_catalog.main.inventory.task_utils.spec_to_ddf import (
    SpecToDDF,
)


class TestSpecToDDF:
    testdata1 = """
    {
        "name": "",
        "description": "",
        "spec": [
            {
                "question_name": "Hobbies",
                "question_description": "Select your hobbies",
                "required": true,
                "type": "multiselect",
                "variable": "hobbies",
                "min": null,
                "max": null,
                "default": "Lawn Tennis\\nCricket",
                "choices": "Cricket\\nTable Tennis\\nLawn Tennis",
                "new_question": true
            }
    ]
    }
    """

    testdata2 = """
    {
        "name": "",
        "description": "",
        "spec": [
           {
                "question_name": "Age",
                "question_description": "Enter your age",
                "required": true,
                "type": "integer",
                "variable": "age",
                "min": 0,
                "max": 100,
                "default": 34,
                "choices": null,
                "new_question": true
            }
        ]
    }
    """

    testdata3 = """
    {
        "name": "",
        "description": "",
        "spec": [
           {
                "question_name": "Enter Temperature",
                "question_description": "Please Enter Temperature",
                "required": true,
                "type": "float",
                "variable": "temperature",
                "min": 0,
                "max": 100,
                "default": 98.6,
                "choices": "",
                "new_question": true
            }
    ]
    }
    """

    testdata4 = """
    {
        "name": "",
        "description": "",
        "spec": [
           {
                "question_name": "Script",
                "question_description": "Your Script",
                "required": true,
                "type": "textarea",
                "variable": "script",
                "min": 0,
                "max": 4096,
                "default": "puts 1",
                "choices": "",
                "new_question": true
            }
         ]
    }
    """

    testdata5 = """
    {
        "name": "",
        "description": "",
        "spec": [
          {
                "question_name": "Password",
                "question_description": "Please enter your password",
                "required": true,
                "type": "password",
                "variable": "blank_password",
                "min": 0,
                "max": 32,
                "default": "$encrypted$",
                "choices": "",
                "new_question": true
            }
           ]
    }
    """

    testdata6 = """
    {
        "name": "",
        "description": "",
        "spec": [
            {
                "question_name": "Username",
                "question_description": "Please enter Username",
                "required": true,
                "type": "text",
                "variable": "username",
                "min": 0,
                "max": 1024,
                "default": "Fred_Flintstone",
                "choices": ["Fred Flintstone","Barney Rubble"],
                "new_question": true
            }
           ]
    }
    """

    testdata7 = """
    {
        "name": "",
        "description": "",
        "spec": [
           {
                "question_name": "Cost Factor",
                "question_description": "Please Select a cost factor",
                "required": true,
                "type": "multiplechoice",
                "variable": "cost_factor",
                "min": null,
                "max": null,
                "default": "34.6",
                "choices": "34.6",
                "new_question": true
            }
           ]
    }
    """

    testdata8 = """
    {
        "name": "",
        "description": "",
        "spec": [
           {
                "question_name": "CPU",
                "question_description": "Select a CPU",
                "required": true,
                "type": "multiplechoice",
                "variable": "cpu",
                "min": null,
                "max": null,
                "default": "",
                "choices": "3"
            }
           ]
    }
    """

    testdata9 = """
    {
        "name": "",
        "description": "",
        "spec": [
           {
                "question_name": "CPU",
                "question_description": "Select a CPU",
                "required": true,
                "type": "multiplechoice",
                "variable": "cpu",
                "min": null,
                "max": null,
                "choices": "3"
            }
           ]
    }
    """
    result1 = {"component": "select-field"}
    result2 = {"dataType": "integer"}
    result3 = {"dataType": "float"}
    result4 = {"component": "textarea-field"}
    result5 = {"component": "text-field"}
    result6 = {"component": "text-field"}
    result7 = {"component": "select-field"}
    result8 = {"component": "select-field"}
    result9 = {"component": "select-field"}

    @pytest.mark.parametrize(
        "test_input,expected",
        [
            (testdata1, result1),
            (testdata2, result2),
            (testdata3, result3),
            (testdata4, result4),
            (testdata5, result5),
            (testdata6, result6),
            (testdata7, result7),
            (testdata8, result8),
            (testdata9, result9),
        ],
    )
    def test_conversion(self, test_input, expected):
        result = SpecToDDF().process(json.loads(test_input))
        item = result["schema"]["fields"][0]
        for k, v in expected.items():
            assert (item[k]) == v
