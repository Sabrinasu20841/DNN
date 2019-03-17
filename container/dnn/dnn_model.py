"""
   Main TensorFlow based Neural Network Model
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse

import tensorflow as tf
from dnn_data import *
import os

parser = argparse.ArgumentParser()
parser.add_argument('--batch-size', default=100, type=int, help='batch size')
parser.add_argument('--train-steps', default=5, type=int,
                    help='number of training steps')
parser.add_argument('--model-dir', default='/opt/ml/model', type=str,
                    help='model home dir')

def weight_variable(shape):
    initial = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(initial)

def bias_variable(shape):
    initial = tf.constant(0.1, shape=shape)
    return tf.Variable(initial)

def conv1d(x, W):
    return tf.nn.conv1d(x, W, 1, padding='SAME')

def max_pool_1d(x, kernel_shape, strides, padding='SAME'):
    return tf.nn.pool(x, kernel_shape, 'MAX', padding=padding, strides=strides)

def R2(real, predicted):
    label_mean = tf.reduce_mean(real, axis=0)
    total_sum_of_square = tf.reduce_sum(tf.square(real - label_mean), axis=0)
    residual_sum_of_square = tf.reduce_sum(tf.square(real - predicted), axis=0)
    r2 = 1 - residual_sum_of_square / total_sum_of_square
    return r2

def Pearson(a, b):
    real = tf.squeeze(a)
    pred = tf.squeeze(b)
    real_new = real - tf.reduce_mean(real)
    pred_new = pred - tf.reduce_mean(real)
    up = tf.reduce_mean(tf.multiply(real_new, pred_new))
    real_var = tf.reduce_mean(tf.multiply(real_new, real_new))
    pred_var = tf.reduce_mean(tf.multiply(pred_new, pred_new))
    down = tf.multiply(tf.sqrt(real_var), tf.sqrt(pred_var))
    return tf.div(up, down)

def dnn_model():
    drug = tf.placeholder(tf.float32, shape=[None, 188, 28])
    cell = tf.placeholder(tf.float32, shape=[None, 735])
    scores = tf.placeholder(tf.float32, shape=[None, 1])
    keep_prob = tf.placeholder(tf.float32)

    drug_conv1_out = 40
    drug_conv1_pool = 3
    drug_conv1_w = weight_variable([7, 28, drug_conv1_out])
    drug_conv1_b = bias_variable([drug_conv1_out])
    drug_conv1_h = tf.nn.relu(conv1d(drug, drug_conv1_w) + drug_conv1_b)
    drug_conv1_p = max_pool_1d(drug_conv1_h, [drug_conv1_pool], [drug_conv1_pool])

    drug_conv2_out = 80
    drug_conv2_pool = 3
    drug_conv2_w = weight_variable([7, drug_conv1_out, drug_conv2_out])
    drug_conv2_b = bias_variable([drug_conv2_out])
    drug_conv2_h = tf.nn.relu(conv1d(drug_conv1_p, drug_conv2_w) + drug_conv2_b)
    drug_conv2_p = max_pool_1d(drug_conv2_h, [drug_conv2_pool], [drug_conv2_pool])

    drug_conv3_out = 60
    drug_conv3_pool = 3
    drug_conv3_w = weight_variable([7, drug_conv2_out, drug_conv3_out])
    drug_conv3_b = bias_variable([drug_conv3_out])
    drug_conv3_h = tf.nn.relu(conv1d(drug_conv2_p, drug_conv3_w) + drug_conv3_b)
    drug_conv3_p = max_pool_1d(drug_conv3_h, [drug_conv3_pool], [drug_conv3_pool])

    cell_conv1_out = 40
    cell_conv1_pool = 3
    cell_tensor = tf.expand_dims(cell, 2)
    cell_conv1_w = weight_variable([7, 1, cell_conv1_out])
    cell_conv1_b = weight_variable([cell_conv1_out])
    cell_conv1_h = tf.nn.relu(conv1d(cell_tensor, cell_conv1_w) + cell_conv1_b)
    cell_conv1_p = max_pool_1d(cell_conv1_h, [cell_conv1_pool], [cell_conv1_pool])

    cell_conv2_out = 80
    cell_conv2_pool = 3
    cell_conv2_w = weight_variable([7, cell_conv1_out, cell_conv2_out])
    cell_conv2_b = bias_variable([cell_conv2_out])
    cell_conv2_h = tf.nn.relu(conv1d(cell_conv1_p, cell_conv2_w) + cell_conv2_b)
    cell_conv2_p = max_pool_1d(cell_conv2_h, [cell_conv2_pool], [cell_conv2_pool])

    cell_conv3_out = 60
    cell_conv3_pool = 3
    cell_conv3_w = weight_variable([7, cell_conv2_out, cell_conv3_out])
    cell_conv3_b = bias_variable([cell_conv3_out])
    cell_conv3_h = tf.nn.relu(conv1d(cell_conv2_p, cell_conv3_w) + cell_conv3_b)
    cell_conv3_p = max_pool_1d(cell_conv3_h, [cell_conv3_pool], [cell_conv3_pool])

    conv_merge = tf.concat([drug_conv3_p, cell_conv3_p], 1)
    shape = conv_merge.get_shape().as_list()
    conv_flat = tf.reshape(conv_merge, [-1, shape[1] * shape[2]])

    fc1_w = weight_variable([shape[1] * shape[2], 1024])
    fc1_b = bias_variable([1024])
    fc1_h = tf.nn.relu(tf.matmul(conv_flat, fc1_w) + fc1_b)
    fc1_drop = tf.nn.dropout(fc1_h, keep_prob)

    fc2_w = weight_variable([1024, 1024])
    fc2_b = bias_variable([1024])
    fc2_h = tf.nn.relu(tf.matmul(fc1_drop, fc2_w) + fc2_b)
    fc2_drop = tf.nn.dropout(fc2_h, keep_prob)

    fc3_w = weight_variable([1024, 1])
    fc3_b = weight_variable([1])

    y_conv = tf.nn.sigmoid(tf.matmul(fc2_drop, fc3_w) + fc3_b)
    loss = tf.losses.mean_squared_error(scores, y_conv)
    train_step = tf.train.AdamOptimizer(1e-4).minimize(loss)

    r_square = R2(scores, y_conv)
    pearson = Pearson(scores, y_conv)
    rmsr = tf.sqrt(loss)

    train, valid, test = load_data(100, ['IC50'])
    saver = tf.train.Saver(var_list=tf.trainable_variables())
    output_file = open("result_all/result_all.txt", "a")

    tf.logging.info("End of Calucation")
    print ("End of Calucation")
    exit() 
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        test_values, test_drugs, test_cells = test.whole_batch()
        valid_values, valid_drugs, valid_cells = valid.whole_batch()
        epoch = 0
        min_loss = 100
        count = 0
        while count < 10:
            train.reset()
            step = 0
            while(train.available()):
                real_values, drug_smiles, cell_muts = train.mini_batch()
                train_step.run(feed_dict={drug:drug_smiles, cell:cell_muts, scores:real_values, keep_prob:0.5})
                step += 1
        valid_loss, valid_r2, valid_p, valid_rmsr = sess.run([loss, r_square, pearson, rmsr], feed_dict={drug:valid_drugs, cell:valid_cells, scores:valid_values, keep_prob:1})
        tf.logging.info("epoch: %d, loss: %g r2: %g pearson: %g rmsr: %g" % (epoch, valid_loss, valid_r2, valid_p, valid_rmsr))
        print("epoch: %d, loss: %g r2: %g pearson: %g rmsr: %g" % (epoch, valid_loss, valid_r2, valid_p, valid_rmsr))
        epoch += 1
        if epoch >5:
            tf.logging.info("End of Calucation")
            print ("End of Calucation")
            exit()
        if valid_loss < min_loss:
            test_loss, test_r2, test_p, test_rmsr = sess.run([loss, r_square, pearson, rmsr], feed_dict={drug:test_drugs, cell:test_cells, scores:test_values, keep_prob:1})
            tf.logging.info("find best, loss: %g r2: %g pearson: %g rmsr: %g ******" % (test_loss, test_r2, test_p, test_rmsr))
            print("find best, loss: %g r2: %g pearson: %g rmsr: %g ******" % (test_loss, test_r2, test_p, test_rmsr))
            os.system("rm model_all/*")
            saver.save(sess, "./model_all/result.ckpt")
            print("saved!")
            min_loss = valid_loss
            count = 0
        else:
            count = count + 1

        if test_r2 > -2:
            output_file.write("%g,%g,%g,%g\n"%(test_loss, test_r2, test_p, test_rmsr))
            tf.logging.info("Saved!!!!!")
            print("Saved!!!!!")
        output_file.close()

        
def main(argv):
    args = parser.parse_args(argv[1:])
    tf.logging.set_verbosity(tf.logging.INFO)
    tf.logging.info("Star main program")
    dnn_model()
    # Fetch the data
    #(train_x, train_y), (test_x, test_y) = iris_data.load_data()

    # Feature columns describe how to use the input.
    #my_feature_columns = []
    #for key in train_x.keys():
        #my_feature_columns.append(tf.feature_column.numeric_column(key=key))

    # Build 2 hidden layer DNN with 10, 10 units respectively.
    #classifier = tf.estimator.Estimator(
    #    model_fn=dnn_model
        #params={
        #    'feature_columns': my_feature_columns,
        #    # Two hidden layers of 10 nodes each.
        #    'hidden_units': [10, 10],
        #    # The model must choose between 3 classes.
        #    'n_classes': 3,
        #}
     #   )

    # Train the Model.
    #classifier.train(
    #    #input_fn=lambda:iris_data.train_input_fn(train_x, train_y, args.batch_size),
    #    steps=args.train-steps)

    # Evaluate the model.
    #eval_result = classifier.evaluate(
        #input_fn=lambda:iris_data.eval_input_fn(test_x, test_y, args.batch_size)
    #    )

    #print('\nTest set accuracy: {accuracy:0.3f}\n'.format(**eval_result))

    # Generate predictions from the model
    #expected = ['Setosa', 'Versicolor', 'Virginica']
    #predict_x = {
    #    'SepalLength': [5.1, 5.9, 6.9],
    #    'SepalWidth': [3.3, 3.0, 3.1],
    #    'PetalLength': [1.7, 4.2, 5.4],
    #    'PetalWidth': [0.5, 1.5, 2.1],
    #}

    #predictions = classifier.predict(
        #input_fn=lambda:iris_data.eval_input_fn(predict_x,
        #                                        labels=None,
        #                                        batch_size=args.batch_size))

    #for pred_dict, expec in zip(predictions, expected):
    #    template = ('\nPrediction is "{}" ({:.1f}%), expected "{}"')

    #    class_id = pred_dict['class_ids'][0]
    #    probability = pred_dict['probabilities'][class_id]

    #    print(template.format(iris_data.SPECIES[class_id],
    #                          100 * probability, expec))


if __name__ == '__main__':
    tf.logging.set_verbosity(tf.logging.DEBUG)
    tf.app.run(main)
       
        
