# MAIA
这个算法的设计目标就是找到DOM中最有可能包含主要内容的"完整片段"，通常这个片段会： 面积足够大（通过lower_bound保证） 结构相对完整（返回完整的父子结构） 内容密度合适（通过面积增量判断）
