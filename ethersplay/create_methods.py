from known_hashes import knownHashes

class CreateMethods(object):

    def __init__(self, view):
        self.seen_bb = set()
        self.view = view

    @staticmethod
    def _get_function_info(bb):
        inss = []
        for ins in bb.__iter__():
            inss.append(ins)

        # IF there is not enough instruction in the bb > not a bb dispacther 
        if len(inss) < 5:
            return None

        (pushHash, _) = inss[-4]
        (eq, _) = inss[-3]
        (push, _) = inss[-2]

        if not str(pushHash[0]).startswith('PUSH'):
            if len(inss) > 4:
                # case where there is another instruction after the push
                # for example a DUP
                (mayPushHash, _ ) = inss[-5]
                if str(mayPushHash[0]).startswith('PUSH'):
                    pushHash = mayPushHash
                else:
                    return None
            else:
                return None
        if not str(eq[0]).startswith('EQ'):
            return None
        if not str(push[0]).startswith('PUSH'):
            return None

        method = str(pushHash[1])
        # we use addr +1, to skip the jumpdest
        # the cfg is more readable like this
        addr = long(str(push[1]), 16) + 1

        return (method, addr)

    def explore(self, bb):
        addr = bb.start
        if addr in self.seen_bb:
            return
        self.seen_bb.add(addr)

        function_info = self._get_function_info(bb)

        if function_info:
            method, addr = function_info

            self.view.create_user_function(addr)
            if method in knownHashes:
                name = knownHashes[method]
            else:
                name = method

            f = self.view.get_function_at(addr)
            f.name = name

        if len(bb.outgoing_edges) == 1:
            son = bb.outgoing_edges[0]
            son = son.target
            self.explore(son)
        else:
            for son in bb.outgoing_edges:
                if son.type.name == 'FalseBranch':
                    son = son.target
                    self.explore(son)


def function_create_methods_start(view, func):
    if func.arch.name != 'evm':
        print "This plugin works only for EVM bytecode"
        return
    create_methods = CreateMethods(view)
    create_methods.explore(func.basic_blocks[0])
