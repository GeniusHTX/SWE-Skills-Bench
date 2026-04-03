"""
Test for 'django-patterns' skill — Saleor ProductReview model & GraphQL mutations
Validates that the Agent implemented a ProductReview Django model, GraphQL
mutations, permissions, and integration with the existing codebase.
"""

import os
import re

import pytest


class TestDjangoPatterns:
    """Verify Django ProductReview model and GraphQL integration in saleor."""

    REPO_DIR = "/workspace/saleor"

    def test_product_review_model_exists(self):
        """ProductReview model must be defined."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"class\s+ProductReview\s*\(.*Model", content):
                        found = True
                        break
            if found:
                break
        assert found, "ProductReview model not found"

    def test_model_has_rating_field(self):
        """ProductReview model must have a rating field."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "ProductReview" in content and re.search(r"rating\s*=\s*models\.", content):
                        found = True
                        break
            if found:
                break
        assert found, "ProductReview model does not have a rating field"

    def test_model_has_foreign_key_to_product(self):
        """ProductReview must have a ForeignKey to Product."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "ProductReview" in content and re.search(r"product\s*=\s*models\.ForeignKey", content):
                        found = True
                        break
            if found:
                break
        assert found, "ProductReview does not have a ForeignKey to Product"

    def test_model_has_user_field(self):
        """ProductReview must have a user/author field."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "ProductReview" in content and re.search(r"(user|author)\s*=\s*models\.ForeignKey", content):
                        found = True
                        break
            if found:
                break
        assert found, "ProductReview does not have a user/author field"

    def test_migration_file_exists(self):
        """A migration file for ProductReview must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "migrations" in root:
                for f in files:
                    if f.endswith(".py") and f != "__init__.py":
                        path = os.path.join(root, f)
                        with open(path, "r", errors="ignore") as fh:
                            content = fh.read()
                        if "ProductReview" in content or "productreview" in content.lower():
                            found = True
                            break
            if found:
                break
        assert found, "No migration file for ProductReview"

    def test_graphql_type_for_review(self):
        """GraphQL type for ProductReview must be defined."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"class\s+ProductReview.*graphene\.|ProductReviewType|ProductReview.*ObjectType", content):
                        found = True
                        break
            if found:
                break
        assert found, "GraphQL type for ProductReview not found"

    def test_create_review_mutation(self):
        """A CreateProductReview or productReviewCreate mutation must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"class\s+(Create|ProductReview\w*Create|ReviewCreate)\w*.*Mutation", content):
                        found = True
                        break
                    if re.search(r"product_review_create|productReviewCreate", content):
                        found = True
                        break
            if found:
                break
        assert found, "Create review mutation not found"

    def test_update_review_mutation(self):
        """An UpdateProductReview or productReviewUpdate mutation must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"class\s+(Update|ProductReview\w*Update|ReviewUpdate)\w*.*Mutation", content):
                        found = True
                        break
                    if re.search(r"product_review_update|productReviewUpdate", content):
                        found = True
                        break
            if found:
                break
        assert found, "Update review mutation not found"

    def test_delete_review_mutation(self):
        """A DeleteProductReview or productReviewDelete mutation must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"class\s+(Delete|ProductReview\w*Delete|ReviewDelete)\w*.*Mutation", content):
                        found = True
                        break
                    if re.search(r"product_review_delete|productReviewDelete", content):
                        found = True
                        break
            if found:
                break
        assert found, "Delete review mutation not found"

    def test_permissions_on_mutations(self):
        """Mutations must enforce permissions."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "ProductReview" in content and re.search(r"permissions?\s*=|permission_classes|@permission_required", content):
                        found = True
                        break
            if found:
                break
        assert found, "No permissions on ProductReview mutations"

    def test_admin_registered(self):
        """ProductReview must be registered in Django admin."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "admin.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "ProductReview" in content:
                        found = True
                        break
            if found:
                break
        assert found, "ProductReview not registered in admin.py"

    def test_review_content_field(self):
        """ProductReview must have a text content field."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "ProductReview" in content and re.search(r"(content|body|text|comment|review_text)\s*=\s*models\.(Text|Char)Field", content):
                        found = True
                        break
            if found:
                break
        assert found, "ProductReview does not have a text content field"
