#!/usr/bin/env python3

from enum import EnumMeta

from decimal import Decimal


class InvalidColumnDefinition(Exception):
    pass


class Column(object):
    """Defined fields (columns) for a given RedisModel.
    """

    def __init__(self, type=str, primary_key=None, composite_key=None, index=None,
                 required=None, enum=None, sort=None):
        """primary_key can exist in only a single column.
        composite_key can exist in multiple columns.
        You can't have both a primary_key and composite_key in the same model.
        index is whether you want this column indexed or not for faster retrieval.
        """
        if type not in (str, int, Decimal):
            # TODO: support for other field types (datetime, uuid, etc)
            err_msg = 'Bad Field Type: {}'.format(type)
            raise InvalidColumnDefinition(err_msg)

        if primary_key and composite_key:
            err_msg = 'Column can be either primary_key or composite_key, but not both'
            raise InvalidColumnDefinition(err_msg)

        self.field_type = type
        self.primary = primary_key is True
        self.composite = composite_key is True
        self.sorted = sort is True
        self.indexed = (index is True) or self.composite
        self.required = required is True or self.primary or self.composite

        self.enum = enum
        if enum:
            if not isinstance(enum, EnumMeta):
                err_msg = '`{}` is not an instance of {}'.format(enum, EnumMeta)
                raise InvalidColumnDefinition(err_msg)
            self.enum_choices = set([x.value for x in enum])
        else:
            self.enum_choices = set()

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.name)


class Integer(Column):
    def __init__(
            self,
            primary_key=None,
            composite_key=None,
            index=None,
            required=None,
            enum=None,
            sort=None,
            auto_increment=False,):
        super(Integer, self).__init__(
            int,
            primary_key=primary_key,
            composite_key=composite_key,
            index=index,
            required=required,
            enum=enum,
            sort=sort,
        )
        self.auto_increment = auto_increment

    async def auto_generate(self, db, model):
        return await db.incr('auto:{}:{}'.format(model.key_prefix(), self.name))


class DecimalColumn(Column):
    
    def __init__(self, decimal_places=10, *kwargs):
        kwargs.pop('type', None)
        kwargs['type'] = Decimal
        self.decimal_places = decimal_places
        super(DecimalColumn, self).__init__(**kwargs)
        
    def get_redis_value(self, decimal_value):
        '''Turns Python native value into Redis Value'''
        if not isinstance(decimal_value, Decimal):
            # we have to do this in case a user passes in a float for filtering, etc...
            decimal_value = Decimal(str(decimal_value))
        return str(int(decimal_value * (10**self.decimal_places)))
    
    def get_python_value(self, redis_value):
        ''' Turns Redis native Value into python value'''
        
        return Decimal(str(redis_value)) / (10**self.decimal_places)
