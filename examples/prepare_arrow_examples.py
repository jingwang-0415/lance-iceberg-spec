"""Generate local reference payloads. Requires PyArrow; never calls a remote service."""
from pathlib import Path
import base64
import json
import pyarrow as pa

root = Path(__file__).resolve().parent / 'fixtures'
root.mkdir(exist_ok=True)
schema = pa.schema([
    pa.field('id', pa.int64(), nullable=False),
    pa.field('customer_name', pa.string()),
    pa.field('price', pa.float64(), metadata={b'unit': b'CNY'}),
    pa.field('description', pa.string()),
    pa.field('embedding', pa.list_(pa.float32(), 3), nullable=False,
             metadata={b'model': b'embedding-v1'}),
    pa.field('legacy_note', pa.string()),
], metadata={b'source': b'example'})

def row(i, price, vector):
    return dict(id=i, customer_name=f'customer-{i}', price=price,
                description=f'order {i}', embedding=vector, legacy_note=None)

def stream(name, rows):
    with pa.OSFile(str(root / name), 'wb') as sink:
        with pa.ipc.new_stream(sink, schema) as writer:
            if rows:
                writer.write_table(pa.Table.from_pylist(rows, schema=schema))
    with pa.memory_map(str(root / name), 'r') as source:
        restored = pa.ipc.open_stream(source).read_all()
    assert restored.schema.equals(schema, check_metadata=True)
    assert restored.num_rows == len(rows)
    return restored.to_pylist()

stream('create-empty.arrow', [])
base = stream('base-data.arrow', [row(1, 100.0, [.1,.2,.3]), row(2,200.0,[.4,.5,.6]), row(3,300.0,[.9,.1,.2])])
insert = stream('insert.arrow', [row(4,400.0,[.2,.3,.4]), row(5,500.0,[.5,.6,.7])])
merge = stream('merge.arrow', [row(1,110.0,[.1,.2,.3]), row(4,400.0,[.2,.3,.4])])

output_schema = pa.schema([pa.field('id',pa.int64(),nullable=False),pa.field('price',pa.float64())])
encoded_schema = base64.b64encode(output_schema.serialize().to_pybytes()).decode('ascii')
decoded_schema = pa.ipc.read_schema(pa.BufferReader(base64.b64decode(encoded_schema)))
assert decoded_schema.equals(output_schema,check_metadata=True)

query_schema=pa.schema([*output_schema,pa.field('_distance',pa.float32())])
query_rows=[{'id':1,'price':100.0,'_distance':0.0},{'id':2,'price':200.0,'_distance':0.27}]
with pa.OSFile(str(root/'query-result.arrow'),'wb') as sink:
    with pa.ipc.new_file(sink,query_schema) as writer:
        writer.write_table(pa.Table.from_pylist(query_rows,schema=query_schema))
with pa.memory_map(str(root/'query-result.arrow'),'r') as source:
    assert pa.ipc.open_file(source).read_all().num_rows==2

metadata=dict(output_schema_base64=encoded_schema,
              schema=str(schema),base_rows=base,insert_rows=insert,merge_rows=merge,
              query_rows=query_rows,
              validation='Arrow stream/file/schema local round-trip passed; no remote call')
(root/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'fixtures':str(root),'arrow_round_trip':'passed'},ensure_ascii=False))
