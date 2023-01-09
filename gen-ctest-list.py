from pathlib import Path
import csv

def gen_modules():
    def recur_gen_modules(module):
        if (module / 'src').exists():
            return [module]
        if not (module / 'pom.xml').exists():
            return []
        return sum(
            map(
                lambda x: recur_gen_modules(x), filter(lambda x: x.is_dir(), list(module.iterdir()))
            ), [])

    return recur_gen_modules(Path('.'))

def main():
    output = open("ctests.csv", 'w')
    writer = csv.writer(output)

    modules = gen_modules()
    for module in modules:
        if (module / 'target' / 'surefire-reports').exists():
            surefire_reports = module / 'target' / 'surefire-reports'
            tests = list(map(lambda x: x.name[5:-4],
                filter(lambda x: x.name.startswith('TEST-'), surefire_reports.iterdir())))
            for test in tests:
                if (surefire_reports / f"{test}-output.txt").exists():
                    with open(surefire_reports / f"{test}-output.txt") as f:
                        for line in f.readline():
                            if line.startswith("[CTEST] Getting property:"):
                                writer.writerow([module.name, test])
                else:
                    pass
                    print(f"{module.name} {test}")
    output.close()



if __name__ == '__main__':
    main()

