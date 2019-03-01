from cluster import *
import sys


def key_value_state_machine(state, input_value):  # only used in Replica class's commit mathod
    if input_value[0] == 'get':
        return state, state.get(input_value[1], None)
    elif input_value[0] == 'set':
        state[input_value[1]] = input_value[2]
        return state, input_value[2]

sequences_running = 0
def do_sequence(network, node, key):
    global sequences_running
    sequences_running += 1  # 共七次running，因为七个nodes，设置七个timers
    reqs = [  # 共6个requests，每个request第一个元素是Requester的input，其中key是a,b,c,d…… 第二个元素是output
        (('get', key), None),
        (('set', key, 10), 10),
        (('get', key), 10),
        (('set', key, 20), 20),
        (('set', key, 30), 30),
        (('get', key), 30),
    ]
    def request():
        if not reqs:  # 每次running遍历regs列表，pop一个，start一个Requester，若列表空，则network停止
            global sequences_running
            sequences_running -= 1  # 每pop一个request，running-1，说明发送request成功
            if not sequences_running:
                network.stop()
            return
        input, exp_output = reqs.pop(0)
        def req_done(output):
            assert output == exp_output, "%r != %r" % (output, exp_output)
            request()
        Requester(node, input, req_done).start()  # node=N6

    network.set_timer(None, 1.0, request)  # set_timer(address, seconds, callback)


def main():
    logging.basicConfig(
        format="%(name)s - %(message)s", level=logging.DEBUG)

    network = Network(int(sys.argv[1]))

    peers = ['N%d' % i for i in range(7)]
    for p in peers:  # 创建集群
        node = network.new_node(address=p)
        if p == 'N0':   # 若是address==0，即第一个node
            Seed(node, initial_state={}, peers=peers, execute_fn=key_value_state_machine)  # 设置为种子机
        else:
            Bootstrap(node, execute_fn=key_value_state_machine, peers=peers).start()  # 不是种子机，通过引导加入集群

    for key in 'abcdefg':
        do_sequence(network, node, key)  # 将node N6放如sequence，设置timer，添加request
    network.run()  # 根据timers列表，每轮发出request

if __name__ == "__main__":
    main()
