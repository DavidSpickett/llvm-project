; RUN: opt < %s -passes="loop-mssa(simple-loop-unswitch)" -verify-memoryssa -disable-output
; PR1559

target triple = "i686-pc-linux-gnu"
	%struct.re_pattern_buffer = type { ptr, i32, i32, i32, ptr, ptr, i32, i8 }

define fastcc i32 @byte_regex_compile(ptr %pattern, i32 %size, i32 %syntax, ptr %bufp) {
entry:
        br i1 false, label %bb147, label %cond_next123

cond_next123:           ; preds = %entry
        ret i32 0

bb147:          ; preds = %entry
        switch i32 0, label %normal_char [
                 i32 91, label %bb1734
                 i32 92, label %bb5700
        ]

bb1734:         ; preds = %bb147
        br label %bb1855.outer.outer

cond_true1831:          ; preds = %bb1855.outer
        br i1 %tmp1837, label %cond_next1844, label %cond_true1840

cond_true1840:          ; preds = %cond_true1831
        ret i32 0

cond_next1844:          ; preds = %cond_true1831
        br i1 false, label %bb1855.outer, label %cond_true1849

cond_true1849:          ; preds = %cond_next1844
        br label %bb1855.outer.outer

bb1855.outer.outer:             ; preds = %cond_true1849, %bb1734
        %b.10.ph.ph = phi ptr [ null, %cond_true1849 ], [ null, %bb1734 ]               ; <ptr> [#uses=1]
        br label %bb1855.outer

bb1855.outer:           ; preds = %bb1855.outer.outer, %cond_next1844
        %b.10.ph = phi ptr [ null, %cond_next1844 ], [ %b.10.ph.ph, %bb1855.outer.outer ]               ; <ptr> [#uses=1]
        %tmp1837 = icmp eq ptr null, null               ; <i1> [#uses=2]
        br i1 false, label %cond_true1831, label %cond_next1915

cond_next1915:          ; preds = %cond_next1961, %bb1855.outer
        store ptr null, ptr null
        br i1 %tmp1837, label %cond_next1929, label %cond_true1923

cond_true1923:          ; preds = %cond_next1915
        ret i32 0

cond_next1929:          ; preds = %cond_next1915
        br i1 false, label %cond_next1961, label %cond_next2009

cond_next1961:          ; preds = %cond_next1929
        %tmp1992 = getelementptr i8, ptr %b.10.ph, i32 0            ; <ptr> [#uses=0]
        br label %cond_next1915

cond_next2009:          ; preds = %cond_next1929
        ret i32 0

bb5700:         ; preds = %bb147
        ret i32 0

normal_char:            ; preds = %bb147
        ret i32 0
}
