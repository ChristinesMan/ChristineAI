# I'm gonna train you up, honey! 
# Let's cuddle! 

from pyAudioAnalysis import audioTrainTest as aT

aT.feature_extraction_train_regression('data', 1.0, 1.0, aT.shortTermWindow, aT.shortTermStep, 'svm_rbf', 'wernicke', False)
