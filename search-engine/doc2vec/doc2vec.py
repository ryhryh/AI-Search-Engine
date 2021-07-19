def get_num_tfrecords():
    import gds
    entityUtil = gds.EntityUtil()
    num_tfrecords = entityUtil.num_tfrecords
    return num_tfrecords

def process(num_tfrecords):
    import dataflow
    dataflowUtil = dataflow.DataflowUtil(runner="DirectRunner", num_tfrecords=num_tfrecords)
    dataflowUtil.run()
    
def update_q():
    import gds
    entityUtil = gds.EntityUtil()
    entityUtil.update_q()
    
if __name__ == '__main__':
    num_tfrecords = get_num_tfrecords()
    print(num_tfrecords)
    
    process(num_tfrecords)
    
    # 確定生成vec之後 update GDS
    print('update_q')
    update_q()
    
    
    
    