import pathlib

ASSET_PATH = pathlib.Path(__file__).resolve().parent / "assets"
main_path = ASSET_PATH / "images" / "Players" / "128x256" / "Blue" / "alienBlue"

print("\n")
print(f"{main_path}_front.png")
print("\n")

for i in range (2):
    print(i+1)