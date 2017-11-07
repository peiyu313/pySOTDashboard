from flask import Flask 
from flask_socketio import SocketIO, send, emit
from threading import Thread



import json
import time

from poap.strategy import FixedSampleStrategy
from poap.strategy import CheckWorkerStrategy
from poap.strategy import InputStrategy

# not sure what i need what i dont
from pySOT import *
from poap.controller import SerialController, ThreadController, BasicWorkerThread
import numpy as np
# not sure what i need what i dont






app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
socketio = SocketIO(app)





def checkering(msg):
    print('---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
    print(str(msg))
    print(msg.params)
    print(msg._status)
    print(msg.value)
    print(msg.status)
    if msg.status != 'pending':
        while 1:
            pass
    return 1


def hiding_this_in_a_function(data, exp_des, surrogate, adapt_samp, maxeval):
    #Step 1
    # Decide how many evaluations we are allowed to use
    #maxeval = 500

    # (1) Optimization problem
    # Use the 10-dimensional Ackley function
    #data = Ackley(dim=10)
    #print(data.info)

    # (2) Experimental design
    # Use a symmetric Latin hypercube with 2d + 1 samples
    #exp_des = SymmetricLatinHypercube(dim=data.dim, npts=2*data.dim+1)

    # (3) Surrogate model
    # Use a cubic RBF interpolant with a linear tail
    #surrogate = RBFInterpolant(kernel=CubicKernel, tail=LinearTail, maxp=maxeval)

    # (4) Adaptive sampling
    # Use DYCORS with 100d candidate points
    #adapt_samp = CandidateDYCORS(data=data, numcand=100*data.dim)




    #Step 2
    # Use the serial controller (uses only one thread)
    controller = SerialController(data.objfunction)

    # (5) Use the sychronous strategy without non-bound constraints
    strategy = SyncStrategyNoConstraints(
            worker_id=0, data=data, maxeval=maxeval, nsamples=1,
            exp_design=exp_des, response_surface=surrogate,
            sampling_method=adapt_samp)
    controller.strategy = strategy
    controller.feval_callbacks = [checkering,]

    # Run the optimization strategy
    result = controller.run()

    # Print the final result
    print('Best value found: {0}'.format(result.value))
    print('Best solution found: {0}'.format(
        np.array_str(result.params[0], max_line_width=np.inf,
                    precision=5, suppress_small=True)))






    #Step 3
    import matplotlib.pyplot as plt

    # Extract function values from the controller
    fvals = np.array([o.value for o in controller.fevals])

    f, ax = plt.subplots()
    ax.plot(np.arange(0,maxeval), fvals, 'bo')  # Points
    ax.plot(np.arange(0,maxeval), np.minimum.accumulate(fvals), 'r-', linewidth=4.0)  # Best value found
    plt.xlabel('Evaluations')
    plt.ylabel('Function Value')
    plt.title(data.info)
    plt.show()








@socketio.on('run')
def onMsgRun(msg):
    msg = '{ "optimization_problem" : {"function" : "Ackley" , "dim" : 10} , "experimental_design" : { "function" : "SymmetricLatinHypercube" , "dim" : 10, "npts" : 21 } , "surrogate_model" : { "function" : "RBFInterpolant" , "maxp" : 500 , "tail" : "LinearTail" , "kernel" : "CubicKernel" } , "adaptive_sampling" : { "function" : "CandidateDYCORS" , "numcand" : 100 , "weights" : -1 } }';

    print(msg)
    parsed_json = json.loads( msg )

    if parsed_json['adaptive_sampling']['weights'] == -1:
        parsed_json['adaptive_sampling']['weights'] = None

    print(parsed_json)

    from obj_make import pySOT_obj, pySOT_class_dict
    new_dict = pySOT_class_dict()
    class_dict = new_dict.get_dict()

    new_obj = pySOT_obj(parsed_json, class_dict)
    [sucess, msg] = new_obj.run()
    if not sucess:
        print(msg+'\n\n\n')
        emit('error_msg', msg)
        return

    # from pySOT_obj import pySOT_obj
    # new_obj = pySOT_obj(parsed_json)
    # [sucess, msg] = new_obj.run()
    # if not sucess:
    #     print(msg+'\n\n\n')
    #     emit('error_msg', msg)
    #     return

    [data, exp_des, surrogate, adapt_samp, maxeval] = new_obj.return_values()

    # from optimization_problems import optimization_problems
    # OP_fun = optimization_problems( parsed_json['optimization_problem'] )
    # data = OP_fun.run()
    print(data.info)
    # print(exp_des)

    # from experimental_designs import experimental_designs
    # ED_fun = experimental_designs( parsed_json['experimental_design'], data.dim )
    # sucess, exp_des = ED_fun.run()
    # if not sucess:
    #     emit('error_msg', exp_des)
    #     return
    # print(exp_des)
    # while 1:
    #     pass
    # from surrogate_models import surrogate_models
    # SM_fun = surrogate_models( parsed_json['surrogate_model'] )
    # surrogate = SM_fun.run()

    # from adaptive_samplings import adaptive_samplings
    # AS_fun = adaptive_samplings(data, parsed_json['adaptive_sampling'])
    # sucess, adapt_samp = AS_fun.run()
    # if not sucess:
    #     emit('error_msg', adapt_samp)
    #     return




    # #hiding_this_in_a_function(data, exp_des, surrogate, adapt_samp, maxeval)
    hiding_this_in_a_function(data, exp_des, surrogate, adapt_samp, parsed_json['surrogate_model']['maxp'])



    return






    from optimization_problems import optimization_problems
    OP_fun = optimization_problems( parsed_json['optimization_problem'] )
    data = OP_fun.run()
    print(data.info)

    from experimental_designs import experimental_designs
    ED_fun = experimental_designs( parsed_json['experimental_design'], data.dim )
    sucess, exp_des = ED_fun.run()
    if not sucess:
        emit('error_msg', exp_des)
        return

    from surrogate_models import surrogate_models
    SM_fun = surrogate_models( parsed_json['surrogate_model'] )
    surrogate = SM_fun.run()

    # (4) 
    # Use DYCORS with 100d candidate points

    from adaptive_samplings import adaptive_samplings
    AS_fun = adaptive_samplings(data, parsed_json['adaptive_sampling'])
    sucess, adapt_samp = AS_fun.run()
    if not sucess:
        emit('error_msg', adapt_samp)
        return

    hiding_this_in_a_function(data, exp_des, surrogate, adapt_samp, parsed_json['surrogate_model']['maxp'])



    ##
    #manager = Manager(init_controller())
    #reactor.callInThread(self.manager.run, self)
    #manager.run()
    ##










def objective(x):
    time.sleep(1)
    return (x-0.123)*(x-0.123)

def init_controller():
    samples = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    controller = ThreadController()
    strategy = FixedSampleStrategy(samples)
    strategy = CheckWorkerStrategy(controller, strategy)
    controller.strategy = strategy

    for _ in range(5):
        worker = BasicWorkerThread(controller, objective)
        controller.launch_worker(worker)
    return controller


class Manager(InputStrategy,Thread):

    def __init__(self, controller, strategy = None):
        print('thread is up----------------------------------------')
        Thread.__init__(self)
        print('thread init running')
        if strategy is None:
            strategy = controller.strategy
        InputStrategy.__init__(self, controller, strategy)
        controller.strategy = self
        print('thread init complete--------------------------------')

    def notify(self, msg):
        print(msg)
        #reactor.callFromThread(self.server.send_notify, msg)
        send(msg, broadcast=True)

    def on_complete(self, rec):
        print('Module run complet---------------------------------')
        self.notify("Completed: {0} -> {1}".format(rec.params, rec.value))
        print('Module complete executed---------------------------')

    def on_kill(self, rec):
        self.notify("Killed: {0}".format(rec.params))

    def on_terminate(self, rec):
        self.notify("Terminating")

    def run(self):
        print('starting new module--------------------------------')
        #self.server = server
        result = self.controller.run()
        if result is None:
            self.notify("No result")
        else:
            self.notify("Result: {0} -> {1}".format(
                result.params, result.value))
        print('Module up and running------------------------------')

@socketio.on('c_connect')
def onConnect(msg):
    print('Message: ' + msg)
    send(msg)

def onMessage(payload, isBinary):
    if isBinary:
        return
        pass

    handlers = {
        'run': self.onMsgRun,
        'terminate': self.onMsgTerminate
    }
    print("Text message received: {0}".format(payload.decode('utf8')))
    msg = json.loads(payload.decode('utf8'))
    handlers[msg['type'].decode('utf8')](msg)

manager = None

@socketio.on('run_')
def onMsgRun(msg):
    print(msg)
    manager = Manager(init_controller())
    #reactor.callInThread(self.manager.run, self)
    manager.run()

@socketio.on('terminate_')
def onMsgTerminate(msg):
    print(msg)
    reactor.callInThread(self.manager.terminate)




@socketio.on('message')
def handleMessage(msg):
    print('Message: ' + msg)
    send(msg, broadcast=True)

@socketio.on('this_event')
def handleMessage(msg):
    print('Message1000: ' + msg)



if __name__ == '__main__':
    import sys
    from twisted.python import log

    log.startLogging(sys.stdout)
    import logging

    logging.basicConfig(level=logging.DEBUG)
    socketio.run(app, debug=True)
    #hiding_this_in_a_function()






 