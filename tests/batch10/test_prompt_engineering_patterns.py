"""
Test for 'prompt-engineering-patterns' skill — Prompt engineering patterns in langchain
Validates that the Agent implemented prompt engineering patterns like
chain-of-thought, few-shot, and structured output within langchain.
"""

import os
import re

import pytest


class TestPromptEngineeringPatterns:
    """Verify prompt engineering pattern implementations in langchain."""

    REPO_DIR = "/workspace/langchain"

    def test_chain_of_thought_prompt(self):
        """Chain-of-thought prompt pattern must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"chain.of.thought|CoT|step.by.step|think.*step|reasoning", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No chain-of-thought prompt found"

    def test_few_shot_prompt(self):
        """Few-shot prompt pattern must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Ff]ew.?[Ss]hot|FewShotPrompt|examples|example_prompt", content):
                        found = True
                        break
            if found:
                break
        assert found, "No few-shot prompt pattern found"

    def test_prompt_template_usage(self):
        """PromptTemplate or ChatPromptTemplate must be used."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"PromptTemplate|ChatPromptTemplate|SystemMessage|HumanMessage", content):
                        found = True
                        break
            if found:
                break
        assert found, "No PromptTemplate usage found"

    def test_structured_output(self):
        """Structured output pattern must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Ss]tructured[Oo]utput|output_parser|[Pp]ydantic|JSON|json_schema|with_structured_output", content):
                        found = True
                        break
            if found:
                break
        assert found, "No structured output pattern found"

    def test_system_prompt_defined(self):
        """System prompt or instruction must be defined."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"system.*prompt|SystemMessage|system_template|role.*system", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No system prompt defined"

    def test_chain_composition(self):
        """Prompts should be composed in chains (LCEL or Chains)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"RunnableSequence|\|.*invoke|LLMChain|chain\s*=|pipe\(", content):
                        found = True
                        break
            if found:
                break
        assert found, "No chain composition found"

    def test_output_parser(self):
        """An output parser must be implemented."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"OutputParser|StrOutputParser|JsonOutputParser|PydanticOutputParser|output_parser", content):
                        found = True
                        break
            if found:
                break
        assert found, "No output parser found"

    def test_variable_substitution(self):
        """Prompts must use variable substitution."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"\{[a-zA-Z_]+\}|input_variables|partial_variables|format_prompt", content):
                        if re.search(r"[Pp]rompt|[Tt]emplate", content):
                            found = True
                            break
            if found:
                break
        assert found, "No variable substitution in prompts"

    def test_example_selector(self):
        """Few-shot patterns should use an example selector."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"ExampleSelector|SemanticSimilarityExampleSelector|example_selector|select_examples", content):
                        found = True
                        break
            if found:
                break
        assert found, "No example selector found"

    def test_model_invocation(self):
        """Code must invoke an LLM model."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"ChatOpenAI|OpenAI|llm\.invoke|model\.invoke|ChatModel|BaseChatModel", content):
                        found = True
                        break
            if found:
                break
        assert found, "No LLM model invocation found"
