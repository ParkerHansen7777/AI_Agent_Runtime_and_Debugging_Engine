import pytest

from agent_runtime.models import BaseModel, FakeModel, ModelResponse

test_responses = [
    ModelResponse(res_type="final", content="This is the final response."),
    ModelResponse(res_type="tool_call", tool_name="add", arguments={"a": 1, "b": 2}),]


def test_model_response_final():
    response = ModelResponse(res_type="final", content="This is the final response.")

    assert response.res_type == "final"
    assert response.content == "This is the final response."
    assert response.tool_name is None
    assert response.arguments is None

def test_model_response_tool_call():
    response = ModelResponse(res_type="tool_call", tool_name="add", arguments={"a": 1, "b": 2})

    assert response.res_type == "tool_call"
    assert response.content is None
    assert response.tool_name == "add"
    assert response.arguments == {"a": 1, "b": 2}

def test_model_response_invalid_res_type():
    with pytest.raises(ValueError):
        ModelResponse(res_type="invalid", content="This should raise an error.")

def test_model_response_missing_content_for_final():
    with pytest.raises(ValueError):
        ModelResponse(res_type="final")

def test_model_response_final_with_tool_name():
    with pytest.raises(ValueError):
        ModelResponse(res_type="final", content="Hello", tool_name="add")

def test_model_response_final_with_arguments():
    with pytest.raises(ValueError):
        ModelResponse(res_type="final", content="Hello", arguments={"a": 1, "b": 2})

def test_model_response_missing_tool_name_for_tool_call():
    with pytest.raises(ValueError):
        ModelResponse(res_type="tool_call", arguments={"a": 1, "b": 2})

def test_model_response_missing_arguments_for_tool_call():
    with pytest.raises(ValueError):
        ModelResponse(res_type="tool_call", tool_name="add")

def test_model_response_tool_call_with_content():
    with pytest.raises(ValueError):
        ModelResponse(res_type="tool_call", content="This should raise an error.", tool_name="add", arguments={"a": 1, "b": 2})

def test_base_model_instantiation():
    with pytest.raises(TypeError):
        BaseModel()  # Should raise TypeError because BaseModel is abstract and cannot be instantiated directly

def test_fake_model_initialization_and_generate():
    test_model = FakeModel(responses=test_responses)
    assert test_model.responses == test_responses
    assert test_model.current_index == 0

def test_fake_model_generate_responses():
    test_model = FakeModel(responses=test_responses)
    assert test_model.generate(instructions="Test instructions", messages=[], tools=[]) == test_responses[0]

    assert test_model.current_index == 1
    assert test_model.generate(instructions="Test instructions", messages=[], tools=[]) == test_responses[1]

    assert test_model.current_index == 2

def test_fake_model_generate_no_more_responses():
    test_model = FakeModel(responses=test_responses)
    test_model.current_index = len(test_responses)  # Simulate that all responses have been used
    with pytest.raises(ValueError):
        test_model.generate(instructions="Test instructions", messages=[], tools=[])  # No more responses available




def test_fake_model_invalid_initialization():
    with pytest.raises(ValueError):
        FakeModel(responses=None)  # Should raise ValueError because responses is None

    with pytest.raises(ValueError):
        FakeModel(responses="not a list")  # Should raise ValueError because responses is not a list

    with pytest.raises(ValueError):
        FakeModel(responses=[1, 2, 3])  # Should raise ValueError because responses is not a list of ModelResponse objects

def test_fake_model_rejects_mixed_response_types():
    with pytest.raises(ValueError):
        FakeModel(responses=[
            ModelResponse(res_type="final", content="Hello"),
            "not a ModelResponse"
        ])