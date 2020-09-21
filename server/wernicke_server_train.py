# I'm gonna train you up, honey! 

from pyAudioAnalysis import audioTrainTest as aT

class_dirs = [
    # "./wernicke_server_training/burp/",
    "./wernicke_server_training/dog/",
    "./wernicke_server_training/lover/",
    # "./wernicke_server_training/lyriq/",
    "./wernicke_server_training/other/",
    "./wernicke_server_training/roxy/",
    "./wernicke_server_training/sex/",
]

aT.extract_features_and_train(class_dirs, 1.0, 1.0, aT.shortTermWindow, aT.shortTermStep, "svm", "wernicke_server_model")

