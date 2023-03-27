:: To run all tests, just run this script. To run a specific test, pass the module path as the only arg.
:: module path example: src.tests.entities.test_inventory.HealingPotionTest.test_entity_has_an_inventory
@echo off
if "%~1"=="" (python -m unittest discover src.tests) else (python -m unittest %1)