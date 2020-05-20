import asyncio

import pytest

from clickplc.mock import ClickPLC


@pytest.fixture
def plc_driver():
    return ClickPLC('fake ip')


@pytest.fixture
def tagged_driver():
    return ClickPLC('fake ip', 'tests/plc_tags.csv')

@pytest.fixture
def expected_tags():
    return {
        'IO2_24V_OK': {'address': {'start': 16397}, 'id': 'C13', 'type': 'bool'},
        'IO2_Module_OK': {'address': {'start': 16396}, 'id': 'C12', 'type': 'bool'},
        'LI_101': {'address': {'start': 428683}, 'id': 'DF6', 'type': 'float'},
        'LI_102': {'address': {'start': 428681}, 'id': 'DF5', 'type': 'float'},
        'P_101': {'address': {'start': 8289}, 'id': 'Y301', 'type': 'bool'},
        'P_101_auto': {'address': {'start': 16385}, 'id': 'C1', 'type': 'bool'},
        'P_102_auto': {'address': {'start': 16386}, 'id': 'C2', 'type': 'bool'},
        'P_103': {'address': {'start': 8290}, 'id': 'Y302', 'type': 'bool'},
        'TIC101_PID_ErrorCode': {'address': {'start': 400100},
                                 'comment': 'PID Error Code',
                                 'id': 'DS100',
                                 'type': 'int16'},
        'TI_101': {'address': {'start': 428673}, 'id': 'DF1', 'type': 'float'},
        'VAHH_101_OK': {'address': {'start': 16395}, 'id': 'C11', 'type': 'bool'},
        'VAH_101_OK': {'address': {'start': 16394}, 'id': 'C10', 'type': 'bool'},
        'VI_101': {'address': {'start': 428685}, 'id': 'DF7', 'type': 'float'}
    }


def test_get_tags(tagged_driver, expected_tags):
    assert expected_tags == tagged_driver.get_tags()


def test_unsupported_tags():
    with pytest.raises(TypeError, match='unsupported data type'):
        ClickPLC('fake ip', 'tests/bad_tags.csv')


@pytest.mark.asyncio
async def test_tagged_driver(tagged_driver, expected_tags):
    await tagged_driver.set('VAH_101_OK', True)
    state = await tagged_driver.get()
    assert state.get('VAH_101_OK') is True
    assert expected_tags.keys() == state.keys()


@pytest.mark.asyncio
@pytest.mark.parametrize('prefix', ['x', 'y'])
async def test_bool_roundtrip(plc_driver, prefix):
    await plc_driver.set(f'{prefix}2', True)
    await plc_driver.set(f'{prefix}3', [False, True])
    expected = {f'{prefix}001': False, f'{prefix}002': True, f'{prefix}003': False,
                f'{prefix}004': True, f'{prefix}005': False}
    assert expected == await plc_driver.get(f'{prefix}1-{prefix}5')


@pytest.mark.asyncio
async def test_c_roundtrip(plc_driver):
    await plc_driver.set('c2', True)
    await plc_driver.set('c3', [False, True])
    expected = {'c1': False, 'c2': True, 'c3': False, 'c4': True, 'c5': False}
    assert expected == await plc_driver.get('c1-c5')


@pytest.mark.asyncio
async def test_df_roundtrip(plc_driver):
    await plc_driver.set('df2', 2.0)
    await plc_driver.set('df3', [3.0, 4.0])
    expected = {'df1': 0.0, 'df2': 2.0, 'df3': 3.0, 'df4': 4.0, 'df5': 0.0}
    assert expected == await plc_driver.get('df1-df5')


@pytest.mark.asyncio
async def test_ds_roundtrip(plc_driver):
    await plc_driver.set('ds2', 2)
    await plc_driver.set('ds3', [3, 4])
    expected = {'ds1': 0, 'ds2': 2, 'ds3': 3, 'ds4': 4, 'ds5': 0}
    assert expected == await plc_driver.get('ds1-ds5')


@pytest.mark.asyncio
async def test_get_error_handling(plc_driver):
    with pytest.raises(ValueError, match='An address must be supplied'):
        await plc_driver.get()
    with pytest.raises(ValueError, match='End address must be greater than start address'):
        await plc_driver.get('c3-c1')
    with pytest.raises(ValueError, match='foo currently unsupported'):
        await plc_driver.get('foo1')
    with pytest.raises(ValueError, match='Inter-category ranges are unsupported'):
        await plc_driver.get('c1-x3')


@pytest.mark.asyncio
async def test_set_error_handling(plc_driver):
    with pytest.raises(ValueError, match='foo currently unsupported'):
        await plc_driver.set('foo1', 1)


@pytest.mark.asyncio
@pytest.mark.parametrize('prefix', ['x', 'y'])
async def test_xy_error_handling(plc_driver, prefix):
    with pytest.raises(ValueError, match='address must be \*01-\*16.'):
        await plc_driver.get(f'{prefix}17')
    with pytest.raises(ValueError, match='address must be in \[001, 816\].'):
        await plc_driver.get(f'{prefix}1001')
    with pytest.raises(ValueError, match='address must be \*01-\*16.'):
        await plc_driver.get(f'{prefix}1-{prefix}17')
    with pytest.raises(ValueError, match='address must be in \[001, 816\].'):
        await plc_driver.get(f'{prefix}1-{prefix}1001')
    with pytest.raises(ValueError, match='address must be \*01-\*16.'):
        await plc_driver.set(f'{prefix}17', True)
    with pytest.raises(ValueError, match='address must be in \[001, 816\].'):
        await plc_driver.set(f'{prefix}1001', True)
    with pytest.raises(ValueError, match='Data list longer than available addresses.'):
        await plc_driver.set(f'{prefix}816', [True, True])


@pytest.mark.asyncio
async def test_c_error_handling(plc_driver):
    with pytest.raises(ValueError, match='C start address must be 1-2000.'):
        await plc_driver.get('c2001')
    with pytest.raises(ValueError, match='C end address must be >start and <2000.'):
        await plc_driver.get('c1-c2001')
    with pytest.raises(ValueError, match='C start address must be 1-2000.'):
        await plc_driver.set('c2001', True)
    with pytest.raises(ValueError, match='Data list longer than available addresses.'):
        await plc_driver.set('c2000', [True, True])


@pytest.mark.asyncio
async def test_df_error_handling(plc_driver):
    with pytest.raises(ValueError, match='DF must be in \[1, 500\]'):
        await plc_driver.get('df501')
    with pytest.raises(ValueError, match='DF end must be in \[1, 500\]'):
        await plc_driver.get('df1-df501')
    with pytest.raises(ValueError, match='DF must be in \[1, 500\]'):
        await plc_driver.set('df501', 1.0)
    with pytest.raises(ValueError, match='Data list longer than available addresses.'):
        await plc_driver.set('df500', [1.0, 2.0])


@pytest.mark.asyncio
async def test_ds_error_handling(plc_driver):
    with pytest.raises(ValueError, match='DS must be in \[1, 4500\]'):
        await plc_driver.get('ds4501')
    with pytest.raises(ValueError, match='DS end must be in \[1, 4500\]'):
        await plc_driver.get('ds1-ds4501')
    with pytest.raises(ValueError, match='DS must be in \[1, 4500\]'):
        await plc_driver.set('ds4501', 1)
    with pytest.raises(ValueError, match='Data list longer than available addresses.'):
        await plc_driver.set('ds4500', [1, 2])


@pytest.mark.asyncio
@pytest.mark.parametrize('prefix', ['x', 'y', 'c'])
async def test_bool_typechecking(plc_driver, prefix):
    with pytest.raises(ValueError, match='Expected .+ as a bool'):
        await plc_driver.set(f'{prefix}1', 1)
    with pytest.raises(ValueError, match='Expected .+ as a bool'):
        await plc_driver.set(f'{prefix}1', [1.0, 1])


@pytest.mark.asyncio
async def test_df_typechecking(plc_driver):
    await plc_driver.set('df1', 1)
    with pytest.raises(ValueError, match='Expected .+ as a float'):
        await plc_driver.set('df1', True)
    with pytest.raises(ValueError, match='Expected .+ as a float'):
        await plc_driver.set('df1', [True, True])


@pytest.mark.asyncio
async def test_ds_typechecking(plc_driver):
    with pytest.raises(ValueError, match='Expected .+ as a int'):
        await plc_driver.set('ds1', 1.0)
    with pytest.raises(ValueError, match='Expected .+ as a int'):
        await plc_driver.set('ds1', True)
    with pytest.raises(ValueError, match='Expected .+ as a int'):
        await plc_driver.set('ds1', [True, True])
