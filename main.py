from acousticbrain.importers import REWTxtImporter
from acousticbrain.analyzers import SPLAnalyzer


importer = REWTxtImporter()

measurement = importer.load("LR.txt")


analyzer = SPLAnalyzer()

result = analyzer.analyze(measurement)


print()

print("===== ANALYSE SPL =====")

print()

for key, value in result.items():

    if isinstance(value, float):
        print(f"{key:20}: {value:.2f}")
    else:
        print(f"{key:20}: {value}")
        