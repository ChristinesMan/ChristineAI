# I'm gonna train you up, honey! 

from pyAudioAnalysis import audioTrainTest as aT

class_dirs = [
    "./wernicke_server_training_single_frame/silence/",
    "./wernicke_server_training_single_frame/not_silence/",
]

aT.extract_features_and_train(class_dirs, 1.0, 1.0, aT.shortTermWindow, aT.shortTermStep, "svm", "wernicke_server_model_single_frame")

