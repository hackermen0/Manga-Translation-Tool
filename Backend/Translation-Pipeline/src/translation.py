import deepl
import os
import dotenv

dotenv.load_dotenv()

deepl_api_key = os.getenv("DEEPL_API_KEY")

translator = deepl.Translator(deepl_api_key)

result = translator.translate_text("", source_lang="JA", target_lang="EN-GB")

print(result)
print(result.text)
