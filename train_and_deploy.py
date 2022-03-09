# I'm gonna train you up, honey! 

from pyAudioAnalysis import audioTrainTest as aT

class_dirs = [
    "./nothing/",
    "./speech_close/",
    "./speech_far/",
    "./laugh/",
    "./hmmm/",
    # "./sex/",
]

aT.extract_features_and_train(class_dirs, 1.0, 1.0, aT.shortTermWindow, aT.shortTermStep, "svm_rbf", "wernicke")
