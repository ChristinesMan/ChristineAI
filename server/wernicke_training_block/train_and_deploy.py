# I'm gonna train you up, honey! 

from pyAudioAnalysis import audioTrainTest as aT

class_dirs = [
    # "./silence/",
    "./ignore/",
    "./lover/",
    "./lover_maybe/",
    # "./keyboard/",
]

aT.extract_features_and_train(class_dirs, 1.0, 1.0, aT.shortTermWindow, aT.shortTermStep, "svm_rbf", "wernicke_block")
