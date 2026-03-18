import json
import sys
from pathlib import Path

# Add the current directory (backend) to sys.path so we can import 'app'
sys.path.append(str(Path(__file__).parent.parent))

from app.main import v1
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def generate_spec(app_instance: FastAPI, version: str, output_path: str):
    """
    Generates an OpenAPI 3.0.3 compatible JSON spec for the given app instance.
    """
    # Create the OpenAPI schema
    # We use a custom version and title for each generated SDK
    openapi_schema = get_openapi(
        title=f"Routine Cloud API {version}",
        version=version,
        description="Routine Cloud API SDK",
        routes=app_instance.routes,
    )

    # OpenAPI 3.1.0 -> 3.0.3 compatibility hack
    # FastAPI 0.100+ defaults to 3.1.0, but many generators prefer 3.0.x
    openapi_schema["openapi"] = "3.0.3"
    
    # Fix 'anyOf' with null which is common in 3.1 but not 3.0
    def fix_anyof_nullable(obj):
        if isinstance(obj, dict):
            if "anyOf" in obj and any(item.get("type") == "null" for item in obj["anyOf"] if isinstance(item, dict)):
                # Convert anyOf: [{type: null}, {type: something}] to nullable: true, type: something
                types = [item for item in obj["anyOf"] if isinstance(item, dict) and item.get("type") != "null"]
                if len(types) == 1:
                    obj.update(types[0])
                    obj["nullable"] = True
                    del obj["anyOf"]
            for key, value in obj.items():
                fix_anyof_nullable(value)
        elif isinstance(obj, list):
            for item in obj:
                fix_anyof_nullable(item)

    fix_anyof_nullable(openapi_schema)

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    print(f"Generated {output_path}")

if __name__ == "__main__":
    # We have version v1
    versions = {
        "v1": v1,
    }
    
    # Base directory for OpenAPI specs (backend / openapi_doc / specs)
    base_dir = Path(__file__).parent.parent / "openapi_doc" / "specs"
    
    for v_name, v_app in versions.items():
        generate_spec(v_app, v_name, str(base_dir / f"openapi-{v_name}.json"))
