from ..language.ast import OperationDefinition
from ..error import GraphQLError
from ..language.visitor import Visitor


class ValidationRule(Visitor):
    def __init__(self, context):
        self.context = context


class UniqueOperationNames(ValidationRule):
    def __init__(self, context):
        super(UniqueOperationNames, self).__init__(context)
        self.known_operation_names = {}

    def enter_OperationDefinition(self, node, *args):
        operation_name = node.name
        if operation_name:
            if operation_name.value in self.known_operation_names:
                return GraphQLError(
                    self.message(operation_name.value),
                    [self.known_operation_names[operation_name.value], operation_name]
                )
            self.known_operation_names[operation_name.value] = operation_name

    @staticmethod
    def message(operation_name):
        return 'There can only be one operation named "{}".'.format(operation_name)


class LoneAnonymousOperation(ValidationRule):
    def __init__(self, context):
        super(LoneAnonymousOperation, self).__init__(context)
        self._op_count = 0

    def enter_Document(self, node, *args):
        n = 0
        for definition in node.definitions:
            if isinstance(definition, OperationDefinition):
                n += 1
        self._op_count = n

    def enter_OperationDefinition(self, node, *args):
        if not node.name and self._op_count > 1:
            return GraphQLError(self.message(), [node])

    @staticmethod
    def message():
        return 'This anonymous operation must be the only defined operation.'


class KnownTypeNames(ValidationRule):
    def enter_NamedType(self, node, *args):
        type_name = node.name.value
        type = self.context.get_schema().get_type(type_name)
        if not type:
            return GraphQLError(self.message(type_name), [node])

    @staticmethod
    def message(type):
        return 'Unknown type "{}".'.format(type)