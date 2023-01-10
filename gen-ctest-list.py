from pathlib import Path
import csv
import xml.etree.ElementTree as ET

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
    output = open("ctests-new.csv", 'w')
    writer = csv.writer(output)
    writer.writerow(['module', 'testClass', 'test'])

    modules = gen_modules()
    for module in modules:
        if (module / 'target' / 'surefire-reports').exists():
            surefire_reports = module / 'target' / 'surefire-reports'
            test_classes = list(map(lambda x: x.name[5:-4],
                filter(lambda x: x.name.startswith('TEST-'), surefire_reports.iterdir())))
            for test_class in test_classes:
                if (surefire_reports / f"{test_class}-output.txt").exists():
                    # we need to first get all the test cases
                    root = ET.parse(surefire_reports / f"TEST-{test_class}.xml").getroot()
                    tests = set(map(lambda x: x.attrib['name'].split('{')[0], filter(lambda x: x.tag == 'testcase', root.iter())))

                    with open(surefire_reports / f"{test_class}-output.txt") as f:
                        ctests = set()
                        stacktrace = 0
                        test_method_called = False
                        test = "$"
                        for idx, line in enumerate(map(lambda x: x.strip(), f.readlines())):
                            if line.startswith("[CTEST] Getting property:"):
                                if not test:
                                    if not test_method_called:
                                        # multi-thread
                                        print(f"{module.relative_to('.')}, {test_class}, null, {idx}")
                                    # a setup method is called (we think that util func is followed by test method)
                                    ctests = tests
                                    break
                                elif test != "$":
                                    assert test in tests, (test, test_class, idx)
                                    ctests.add(test)
                                test = ""
                                stacktrace = 2
                                test_method_called = False
                            elif stacktrace:
                                if not line.startswith("at "):
                                    stacktrace -= 1
                                    continue
                                line = line[3:].split('(')[0]
                                if line.startswith(test_class):
                                    if line[len(test_class):].startswith('.test'):
                                        test_method_called = True
                                        test = line[len(test_class)+1:].split('$')[0]
                                    elif line[len(test_class):].startswith('.lambda$test'):
                                        test_method_called = True
                                        test = line[len(test_class)+8:].split('$')[0]
                                    elif line[len(test_class)] == "$":
                                        # may be multiThreaded, need to see if there's any usable info later
                                        pass
                                    else:
                                        # could be a util func or a setup method
                                        test_method_called = True
                                        pass

                    if test and test != "$":
                        ctests.add(test)
                        assert test in tests, (test, test_class, idx)

                    for ctest in ctests:
                        writer.writerow([module.relative_to('.'), test_class, ctest])

                else:
                    pass
                    #print(f"{module.name} {test}")

    output.close()



if __name__ == '__main__':
    main()

