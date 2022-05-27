import keras
from keras.layers import Dense, GlobalAveragePooling2D
from keras import Input, Model
from keras.callbacks import EarlyStopping
from keras.applications.xception import Xception
from sklearn.metrics import r2_score
import numpy as np

def test_model(model) -> None:

	'''Tests the models based on never seen data and their labels'''

	# Load pre normalized and numpy-fied examples and their labels, examples are of shape (256, 256, 3)
	test_examples = np.array(np.load("augmented_testdata_x.npy"))	# Normalized to between -1 and 1
	test_labels = np.array(np.load("augmented_testdata_y.npy"))		# Normalized to between 0 and 1

	# Predict IWI based on the test examples in order to compare it to the real IWI
	pred_values = np.squeeze(model.predict(test_examples))
	true_values = test_labels

	# Get the root mean squared error for the test examples
	rmse = np.sqrt(model.evaluate(test_examples, test_labels, verbose = 0))

	print("Test RMSE: {:.5f}".format(rmse))

	r2 = r2_score(true_values, pred_values)

	print("Test R^2 Score: {:.5f}".format(r2))
	print("Predicted: " + str(pred_values))
	print("True: " + str(true_values))

def get_model(
			  batch_size = 16,			# 16 in order to compute faster on the GPU, 2 times the amount of physical processors
			  epochs = 200,				# Number of training epochs
			  shape = (256, 256, 3),	# Define the shape of the data to be used, must be squared
			  val_split = 0.30,			# What percentage of the training data that should be used for validation
			  stop_patience = 20		# How many epochs to wait before stopping if the validation loss is getting worse
			  ):

	'''Returns a trained tensorflow model based on MAXAR:s dataset.'''

	# Load pre normalized and numpy-fied examples and their labels, examples are of shape (256, 256, 3)
	training_examples = np.array(np.load("augmented_data_x.npy"))	# Normalized to between -1 and 1
	training_labels = np.array(np.load("augmented_data_y.npy"))		# Normalized to between 0 and 1

	# Instantiate a Keras tensor
	inputs = Input(shape = shape)

	# Convolute the inputs with Xception, changes the shape from (256, 256, 3) into (8, 8, 2048)
	x = Xception(
				 weights = None,       	# Don't use the inbuilt pre-trained weights  
				 include_top = False,  	# Shape isn't default (299, 299, 3) 
				 input_shape = shape,  	# Define shape
				 )(inputs)

	# Pool the output from Xception, changing the shape from (8, 8, 2048)
	x = GlobalAveragePooling2D()(x)

	# Build up the neural network structure by creating all the dense layers 
	x = Dense(1024, activation = 'relu')(x)	# relu is best in between layers
	x = Dense(512, activation = 'relu')(x)
	x = Dense(256, activation = 'relu')(x)
	x = Dense(128, activation = 'relu')(x)
	x = Dense(64, activation = 'relu')(x)
	x = Dense(32, activation = 'relu')(x)
	x = Dense(16, activation = 'relu')(x)
	x = Dense(4, activation = 'relu')(x)
	output = Dense(1, activation='linear')(x)	# Create a single output neuron, linear since it is a regression nn

	# Build the model based on the already defined inputs and outputs
	model = Model(inputs = inputs, outputs = output)

	model.summary()		# Print out a summary of the model structure
	model.compile(
				  optimizer = 'adam',	# Use the optimizer Adam, good for big datasets with many paramaters
				  loss = 'mse'			# Use mean squared error as the loss function
				  )

	# The callback function stops the training if the validation loss has been getting worse for a set amount of epochs
	callback = [EarlyStopping(monitor = 'val_loss', 		# What to monitor
							  patience = stop_patience,		# How many epochs to wait 
							  restore_best_weights=True		# If it stops, restore the best weights
							  )]

	# Train the model with the fit-function and save the history as a variable
	historyobject = model.fit(
							  training_examples,
							  training_labels,				
							  validation_split = val_split,	# Percentage of training to validate with  
							  epochs = epochs,				# How many epochs to train for
							  batch_size = batch_size,		# What batch size to group the data into
							  callbacks = callback			# Use the callback function
							  )

	# Return the model and the training history
	return model, historyobject.history

if __name__ == '__main__':

	# Get the model and its training history
	model, history = get_model()

	# Save all usefull data
	model.save("xception_model.tf")		# Save the model
	np.save('history.npy', history)		# Save the history

	# Check the model accuracy on never seen data
	test_model(model)