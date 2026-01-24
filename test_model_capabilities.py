import json
import os

def test_model_capabilities():
    dir_path = 'configs/text-models/'
    for filename in os.listdir(dir_path):
        if filename.endswith('.json'):
            filepath = os.path.join(dir_path, filename)
            with open(filepath, 'r') as f:
                data = json.load(f)
            print(f"\nTesting models in {filename}:")
            for model in data:
                model_name = model.get('model_name', 'Unknown')
                settings = model.get('settings', {})
                tools_support = settings.get('tools_support', False)
                vision_support = settings.get('vision_support', False)
                print(f"  {model_name}: Tools support = {tools_support}, Vision support = {vision_support}")
                # Here you can add assertions or further checks
                assert isinstance(tools_support, bool), f"tools_support should be bool for {model_name}"
                assert isinstance(vision_support, bool), f"vision_support should be bool for {model_name}"

if __name__ == "__main__":
    test_model_capabilities()