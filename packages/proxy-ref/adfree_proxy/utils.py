"""Funciones auxiliares comunes"""
import json


def load_yaml(path: str):
    import yaml
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def read_rules(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
