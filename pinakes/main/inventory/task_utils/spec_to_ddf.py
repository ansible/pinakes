"""Convert a Tower Survey Spec to
    Data Driven Forms (DDF) format
"""


class SpecToDDF:
    DDF_FIELD_TYPES = {
        "multiplechoice": {"component": "select-field"},
        "multiselect": {"component": "select-field", "multi": True},
        "text": {"component": "text-field"},
        "integer": {
            "component": "text-field",
            "type": "number",
            "dataType": "integer",
        },
        "float": {
            "component": "text-field",
            "type": "number",
            "dataType": "float",
        },
        "password": {"component": "text-field", "type": "password"},
        "textarea": {"component": "textarea-field"},
    }

    def process(self, data):
        """Convert to DDF"""
        ddf_fields = []
        for field in data["spec"]:
            ddf_fields.append(self._convertField(field))

        schema = {}
        schema["fields"] = ddf_fields
        schema["title"] = data["name"]
        schema["description"] = data["description"]

        result = {"schemaType": "default", "schema": schema}
        return result

    def _convertField(self, field):
        result = {
            "label": field["question_name"],
            "name": field["variable"],
            "helperText": field.get("question_description", ""),
            "isRequired": field["required"],
        }
        result = {**result, **self.DDF_FIELD_TYPES[field["type"]]}

        value = self._getOptions(field)
        if len(value) > 0:
            result["options"] = value

        value = self._getValidateArray(field)
        if len(value) > 0:
            result["validate"] = value

        if "multi" in result:
            result["initialValue"] = field.get("default", "").split("\n")
        else:
            result["initialValue"] = field.get("default", "")

        return result

    def _getOptions(self, field):
        values = None
        if "choices" in field:
            if isinstance(field["choices"], list):
                values = field["choices"]
            elif isinstance(field["choices"], str) and field["choices"] != "":
                values = field["choices"].split("\n")
            else:
                return []
        else:
            return []

        result = []
        for v in values:
            result.append({"label": v, "value": v})
        return result

    def _getValidateArray(self, field):
        result = []
        if field["required"]:
            result.append({"type": "required-validator"})

        if "min" in field:
            if (
                field["type"] == "text"
                or field["type"] == "password"
                or field["type"] == "textarea"
            ):
                result.append(
                    {"type": "min-length-validator", "threshold": field["min"]}
                )
            elif field["type"] == "integer" or field["type"] == "float":
                result.append(
                    {"type": "min-number-value", "value": field["min"]}
                )

        if "max" in field:
            if (
                field["type"] == "text"
                or field["type"] == "password"
                or field["type"] == "textarea"
            ):
                result.append(
                    {"type": "max-length-validator", "threshold": field["max"]}
                )
            elif field["type"] == "integer" or field["type"] == "float":
                result.append(
                    {"type": "max-number-value", "value": field["max"]}
                )

        return result
