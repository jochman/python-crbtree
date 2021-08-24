import os
import re

from cffi import FFI


SRC_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rb_tree')

FFI_BUILDER = FFI()

HEADER = '''
extern "Python" int rb_tree_node_compare(struct rb_tree *self, struct rb_node *a, struct rb_node *b);
extern "Python" void rb_tree_node_was_removed(struct rb_tree *self, struct rb_node *node);

typedef int  (*rb_tree_node_cmp_f) (struct rb_tree *self, struct rb_node *a, struct rb_node *b);
typedef void (*rb_tree_node_f)     (struct rb_tree *self, struct rb_node *node);

struct rb_node {
    int             red;     // Color red (1), black (0)
    struct rb_node *link[2]; // Link left [0] and right [1]
    void           *value;   // User provided, used indirectly via rb_tree_node_cmp_f.
};

struct rb_tree {
    struct rb_node    *root;
    rb_tree_node_cmp_f cmp;
    size_t             size;
    void              *info; // User provided, not used by rb_tree.
};

struct rb_iter {
    struct rb_tree *tree;
    struct rb_node *node;                     // Current node
    struct rb_node *path[RB_ITER_MAX_HEIGHT]; // Traversal path
    size_t          top;                      // Top of stack
    void           *info;                     // User provided, not used by rb_iter.
};

int             rb_tree_node_cmp_ptr_cb (struct rb_tree *self, struct rb_node *a, struct rb_node *b);
void            rb_tree_node_dealloc_cb (struct rb_tree *self, struct rb_node *node);

struct rb_tree *rb_tree_create          (rb_tree_node_cmp_f cmp);
void            rb_tree_dealloc         (struct rb_tree *self, rb_tree_node_f node_cb);
void           *rb_tree_find            (struct rb_tree *self, void *value);
int             rb_tree_insert          (struct rb_tree *self, void *value);
int             rb_tree_remove          (struct rb_tree *self, void *value);
size_t          rb_tree_size            (struct rb_tree *self);

int             rb_tree_remove_with_cb  (struct rb_tree *self, void *value, rb_tree_node_f node_cb);

struct rb_iter *rb_iter_alloc           (void);
struct rb_iter *rb_iter_create          (void);
void            rb_iter_dealloc         (struct rb_iter *self);
void           *rb_iter_first           (struct rb_iter *self, struct rb_tree *tree);
void           *rb_iter_next            (struct rb_iter *self);
'''

MACROS = {
    'RB_ITER_MAX_HEIGHT': '64'
}
for macro_name, macro_value in MACROS.items():
    HEADER = re.sub(r'\b{}\b'.format(re.escape(macro_name)), re.escape(macro_value), HEADER)

FFI_BUILDER.cdef(HEADER)
FFI_BUILDER.set_source('crbtree._rbtree', '''
#define RB_ITER_MAX_HEIGHT 64
#include "rb_tree.c"
''', include_dirs=[SRC_ROOT])

if __name__ == '__main__':
    FFI_BUILDER.compile()
