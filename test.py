import requests

URL = "http://127.0.0.1:8000/run"

# Test cases: each is (name, payload_data)
# Format: "x,y,direction,index;..." where direction = T(OP), B(OTTOM), L(EFT), R(IGHT)
# x, y must be multiples of 10 with offset 5 (e.g., 5, 15, 25, 35, ...)
TEST_CASES = [
    # Original
    (
        "Original - 5 obstacles",
        "85,75,B,2;25,75,T,2;75,165,B,3;145,35,T,4;155,155,L,5",
    ),
    # Minimal - single obstacle
    (
        "Minimal - single obstacle",
        "75,25,T,1",
    ),
    # Two obstacles, spaced apart
    (
        "Two obstacles - vertical separation",
        "75,25,T,1;75,165,B,2",
    ),
    (
        "Two obstacles - horizontal separation",
        "25,95,L,1;165,95,R,2",
    ),
    # Three obstacles - different directions
    (
        "Three obstacles - mixed directions",
        "55,55,T,1;125,55,B,2;95,135,L,3",
    ),
    # Four obstacles - grid layout
    (
        "Four obstacles - corners",
        "35,35,T,1;165,35,T,2;35,165,B,3;165,165,B,4",
    ),
    # Five obstacles - from main.py layout
    (
        "Five obstacles - main.py layout",
        "75,25,T,2;125,75,L,3;35,145,T,4;95,155,R,5;155,115,T,6",
    ),
    # Six obstacles - denser
    (
        "Six obstacles - denser layout",
        "45,45,T,1;95,45,T,2;145,45,T,3;45,115,R,4;95,145,T,5;145,115,T,6",
    ),
    # Seven obstacles
    (
        "Seven obstacles - scattered",
        "35,25,T,1;95,65,B,2;155,45,T,3;55,95,L,4;135,95,R,5;75,145,T,6;115,165,B,7",
    ),
    # Eight obstacles - maximum density for small grid
    (
        "Eight obstacles - full grid",
        "45,25,T,1;95,45,T,2;145,25,T,3;45,95,R,4;145,95,R,5;45,185,B,6;95,145,T,7;145,175,L,8",
    ),
]


def run_test(name: str, data: str) -> dict:
    """Run a single test case and return result."""
    try:
        response = requests.post(URL, json={"data": data}, timeout=120)
        return {
            "name": name,
            "status": response.status_code,
            "response": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
            "success": response.status_code == 200,
        }
    except requests.exceptions.ConnectionError:
        return {"name": name, "status": None, "response": "Connection refused - is the server running?", "success": False}
    except requests.exceptions.Timeout:
        return {"name": name, "status": None, "response": "Request timed out", "success": False}
    except Exception as e:
        return {"name": name, "status": None, "response": str(e), "success": False}


def main():
    import sys

    print("Running API tests against", URL)
    print("-" * 60)

    # Optional: run specific test by index, e.g. python test.py 0
    cases = TEST_CASES
    if len(sys.argv) > 1:
        idx = int(sys.argv[1])
        cases = [TEST_CASES[idx]]

    results = []
    for name, data in cases:
        result = run_test(name, data)
        results.append(result)
        status_str = "PASS" if result["success"] else "FAIL"
        print(f"[{status_str}] {name}")
        print(f"      Status: {result['status']}, Response: {result['response']}")

    print("-" * 60)
    passed = sum(1 for r in results if r["success"])
    print(f"Results: {passed}/{len(results)} tests passed")


if __name__ == "__main__":
    main()
