; NOTE: Assertions have been autogenerated by utils/update_test_checks.py UTC_ARGS: --version 5
; RUN: opt -p constraint-elimination -S %s | FileCheck %s

declare void @llvm.assume(i1)

define i1 @multi_exiting_loop_eq_same_unique_exit_const_compare_known(ptr %s) {
; CHECK-LABEL: define i1 @multi_exiting_loop_eq_same_unique_exit_const_compare_known(
; CHECK-SAME: ptr [[S:%.*]]) {
; CHECK-NEXT:  [[ENTRY:.*]]:
; CHECK-NEXT:    br label %[[LOOP_HEADER:.*]]
; CHECK:       [[LOOP_HEADER]]:
; CHECK-NEXT:    [[IV:%.*]] = phi i32 [ 0, %[[ENTRY]] ], [ [[IV_NEXT:%.*]], %[[LOOP_LATCH:.*]] ]
; CHECK-NEXT:    [[EXITCOND_NOT:%.*]] = icmp eq i32 [[IV]], 1234
; CHECK-NEXT:    br i1 [[EXITCOND_NOT]], label %[[EXIT:.*]], label %[[LOOP_LATCH]]
; CHECK:       [[LOOP_LATCH]]:
; CHECK-NEXT:    [[ARRAYIDX:%.*]] = getelementptr inbounds i8, ptr [[S]], i32 [[IV]]
; CHECK-NEXT:    [[TMP0:%.*]] = load i8, ptr [[ARRAYIDX]], align 1
; CHECK-NEXT:    [[LATCH_C:%.*]] = icmp ult i8 [[TMP0]], 10
; CHECK-NEXT:    [[IV_NEXT]] = add nuw nsw i32 [[IV]], 1
; CHECK-NEXT:    br i1 [[LATCH_C]], label %[[LOOP_HEADER]], label %[[EXIT]]
; CHECK:       [[EXIT]]:
; CHECK-NEXT:    [[T:%.*]] = icmp ult i32 [[IV]], 1235
; CHECK-NEXT:    ret i1 [[T]]
;
entry:
  br label %loop.header

loop.header:
  %iv = phi i32 [ 0, %entry ], [ %iv.next, %loop.latch ]
  %exitcond.not = icmp eq i32 %iv, 1234
  br i1 %exitcond.not, label %exit, label %loop.latch

loop.latch:
  %arrayidx = getelementptr inbounds i8, ptr %s, i32 %iv
  %0 = load i8, ptr %arrayidx, align 1
  %latch.c = icmp ult i8 %0, 10
  %iv.next = add nuw nsw i32 %iv, 1
  br i1 %latch.c, label %loop.header, label %exit

exit:
  %t = icmp ult i32 %iv, 1235
  ret i1 %t
}

define i1 @multi_exiting_loop_eq_same_unique_exit_const_compare_not_known_due_to_start_value(ptr %s) {
; CHECK-LABEL: define i1 @multi_exiting_loop_eq_same_unique_exit_const_compare_not_known_due_to_start_value(
; CHECK-SAME: ptr [[S:%.*]]) {
; CHECK-NEXT:  [[ENTRY:.*]]:
; CHECK-NEXT:    br label %[[LOOP_HEADER:.*]]
; CHECK:       [[LOOP_HEADER]]:
; CHECK-NEXT:    [[IV:%.*]] = phi i32 [ 1235, %[[ENTRY]] ], [ [[IV_NEXT:%.*]], %[[LOOP_LATCH:.*]] ]
; CHECK-NEXT:    [[EXITCOND_NOT:%.*]] = icmp eq i32 [[IV]], 1234
; CHECK-NEXT:    br i1 [[EXITCOND_NOT]], label %[[EXIT:.*]], label %[[LOOP_LATCH]]
; CHECK:       [[LOOP_LATCH]]:
; CHECK-NEXT:    [[ARRAYIDX:%.*]] = getelementptr inbounds i8, ptr [[S]], i32 [[IV]]
; CHECK-NEXT:    [[TMP0:%.*]] = load i8, ptr [[ARRAYIDX]], align 1
; CHECK-NEXT:    [[LATCH_C:%.*]] = icmp ult i8 [[TMP0]], 10
; CHECK-NEXT:    [[IV_NEXT]] = add i32 [[IV]], 1
; CHECK-NEXT:    br i1 [[LATCH_C]], label %[[LOOP_HEADER]], label %[[EXIT]]
; CHECK:       [[EXIT]]:
; CHECK-NEXT:    [[T:%.*]] = icmp ult i32 [[IV]], 1235
; CHECK-NEXT:    ret i1 [[T]]
;
entry:
  br label %loop.header

loop.header:
  %iv = phi i32 [ 1235, %entry ], [ %iv.next, %loop.latch ]
  %exitcond.not = icmp eq i32 %iv, 1234
  br i1 %exitcond.not, label %exit, label %loop.latch

loop.latch:
  %arrayidx = getelementptr inbounds i8, ptr %s, i32 %iv
  %0 = load i8, ptr %arrayidx, align 1
  %latch.c = icmp ult i8 %0, 10
  %iv.next = add i32 %iv, 1
  br i1 %latch.c, label %loop.header, label %exit

exit:
  %t = icmp ult i32 %iv, 1235
  ret i1 %t
}

define i1 @multi_exiting_loop_eq_same_unique_exit_const_compare_known_due_to_precond_on_start_value(ptr %s, i32 %start) {
; CHECK-LABEL: define i1 @multi_exiting_loop_eq_same_unique_exit_const_compare_known_due_to_precond_on_start_value(
; CHECK-SAME: ptr [[S:%.*]], i32 [[START:%.*]]) {
; CHECK-NEXT:  [[ENTRY:.*]]:
; CHECK-NEXT:    [[PRE_C:%.*]] = icmp ule i32 [[START]], 1234
; CHECK-NEXT:    call void @llvm.assume(i1 [[PRE_C]])
; CHECK-NEXT:    br label %[[LOOP_HEADER:.*]]
; CHECK:       [[LOOP_HEADER]]:
; CHECK-NEXT:    [[IV:%.*]] = phi i32 [ [[START]], %[[ENTRY]] ], [ [[IV_NEXT:%.*]], %[[LOOP_LATCH:.*]] ]
; CHECK-NEXT:    [[EXITCOND_NOT:%.*]] = icmp eq i32 [[IV]], 1234
; CHECK-NEXT:    br i1 [[EXITCOND_NOT]], label %[[EXIT:.*]], label %[[LOOP_LATCH]]
; CHECK:       [[LOOP_LATCH]]:
; CHECK-NEXT:    [[ARRAYIDX:%.*]] = getelementptr inbounds i8, ptr [[S]], i32 [[IV]]
; CHECK-NEXT:    [[TMP0:%.*]] = load i8, ptr [[ARRAYIDX]], align 1
; CHECK-NEXT:    [[LATCH_C:%.*]] = icmp ult i8 [[TMP0]], 10
; CHECK-NEXT:    [[IV_NEXT]] = add i32 [[IV]], 1
; CHECK-NEXT:    br i1 [[LATCH_C]], label %[[LOOP_HEADER]], label %[[EXIT]]
; CHECK:       [[EXIT]]:
; CHECK-NEXT:    [[T:%.*]] = icmp ult i32 [[IV]], 1235
; CHECK-NEXT:    ret i1 [[T]]
;
entry:
  %pre.c = icmp ule i32 %start, 1234
  call void @llvm.assume(i1 %pre.c)
  br label %loop.header

loop.header:
  %iv = phi i32 [ %start, %entry ], [ %iv.next, %loop.latch ]
  %exitcond.not = icmp eq i32 %iv, 1234
  br i1 %exitcond.not, label %exit, label %loop.latch

loop.latch:
  %arrayidx = getelementptr inbounds i8, ptr %s, i32 %iv
  %0 = load i8, ptr %arrayidx, align 1
  %latch.c = icmp ult i8 %0, 10
  %iv.next = add i32 %iv, 1
  br i1 %latch.c, label %loop.header, label %exit

exit:
  %t = icmp ult i32 %iv, 1235
  ret i1 %t
}

define i1 @multi_exiting_loop_eq_same_unique_exit_const_compare_not_known_due_to_precond_on_start_value(ptr %s, i32 %start) {
; CHECK-LABEL: define i1 @multi_exiting_loop_eq_same_unique_exit_const_compare_not_known_due_to_precond_on_start_value(
; CHECK-SAME: ptr [[S:%.*]], i32 [[START:%.*]]) {
; CHECK-NEXT:  [[ENTRY:.*]]:
; CHECK-NEXT:    [[PRE_C:%.*]] = icmp ule i32 [[START]], 1236
; CHECK-NEXT:    call void @llvm.assume(i1 [[PRE_C]])
; CHECK-NEXT:    br label %[[LOOP_HEADER:.*]]
; CHECK:       [[LOOP_HEADER]]:
; CHECK-NEXT:    [[IV:%.*]] = phi i32 [ [[START]], %[[ENTRY]] ], [ [[IV_NEXT:%.*]], %[[LOOP_LATCH:.*]] ]
; CHECK-NEXT:    [[EXITCOND_NOT:%.*]] = icmp eq i32 [[IV]], 1234
; CHECK-NEXT:    br i1 [[EXITCOND_NOT]], label %[[EXIT:.*]], label %[[LOOP_LATCH]]
; CHECK:       [[LOOP_LATCH]]:
; CHECK-NEXT:    [[ARRAYIDX:%.*]] = getelementptr inbounds i8, ptr [[S]], i32 [[IV]]
; CHECK-NEXT:    [[TMP0:%.*]] = load i8, ptr [[ARRAYIDX]], align 1
; CHECK-NEXT:    [[LATCH_C:%.*]] = icmp ult i8 [[TMP0]], 10
; CHECK-NEXT:    [[IV_NEXT]] = add i32 [[IV]], 1
; CHECK-NEXT:    br i1 [[LATCH_C]], label %[[LOOP_HEADER]], label %[[EXIT]]
; CHECK:       [[EXIT]]:
; CHECK-NEXT:    [[T:%.*]] = icmp ult i32 [[IV]], 1236
; CHECK-NEXT:    ret i1 [[T]]
;
entry:
  %pre.c = icmp ule i32 %start, 1236
  call void @llvm.assume(i1 %pre.c)
  br label %loop.header

loop.header:
  %iv = phi i32 [ %start, %entry ], [ %iv.next, %loop.latch ]
  %exitcond.not = icmp eq i32 %iv, 1234
  br i1 %exitcond.not, label %exit, label %loop.latch

loop.latch:
  %arrayidx = getelementptr inbounds i8, ptr %s, i32 %iv
  %0 = load i8, ptr %arrayidx, align 1
  %latch.c = icmp ult i8 %0, 10
  %iv.next = add i32 %iv, 1
  br i1 %latch.c, label %loop.header, label %exit

exit:
  %t = icmp ult i32 %iv, 1236
  ret i1 %t
}

define i1 @multi_exiting_loop_eq_same_unique_exit_const_compare_not_known_due_to_missing_precond(ptr %s, i32 %start) {
; CHECK-LABEL: define i1 @multi_exiting_loop_eq_same_unique_exit_const_compare_not_known_due_to_missing_precond(
; CHECK-SAME: ptr [[S:%.*]], i32 [[START:%.*]]) {
; CHECK-NEXT:  [[ENTRY:.*]]:
; CHECK-NEXT:    br label %[[LOOP_HEADER:.*]]
; CHECK:       [[LOOP_HEADER]]:
; CHECK-NEXT:    [[IV:%.*]] = phi i32 [ [[START]], %[[ENTRY]] ], [ [[IV_NEXT:%.*]], %[[LOOP_LATCH:.*]] ]
; CHECK-NEXT:    [[EXITCOND_NOT:%.*]] = icmp eq i32 [[IV]], 1234
; CHECK-NEXT:    br i1 [[EXITCOND_NOT]], label %[[EXIT:.*]], label %[[LOOP_LATCH]]
; CHECK:       [[LOOP_LATCH]]:
; CHECK-NEXT:    [[ARRAYIDX:%.*]] = getelementptr inbounds i8, ptr [[S]], i32 [[IV]]
; CHECK-NEXT:    [[TMP0:%.*]] = load i8, ptr [[ARRAYIDX]], align 1
; CHECK-NEXT:    [[LATCH_C:%.*]] = icmp ult i8 [[TMP0]], 10
; CHECK-NEXT:    [[IV_NEXT]] = add i32 [[IV]], 1
; CHECK-NEXT:    br i1 [[LATCH_C]], label %[[LOOP_HEADER]], label %[[EXIT]]
; CHECK:       [[EXIT]]:
; CHECK-NEXT:    [[T:%.*]] = icmp ult i32 [[IV]], 1236
; CHECK-NEXT:    ret i1 [[T]]
;
entry:
  br label %loop.header

loop.header:
  %iv = phi i32 [ %start, %entry ], [ %iv.next, %loop.latch ]
  %exitcond.not = icmp eq i32 %iv, 1234
  br i1 %exitcond.not, label %exit, label %loop.latch

loop.latch:
  %arrayidx = getelementptr inbounds i8, ptr %s, i32 %iv
  %0 = load i8, ptr %arrayidx, align 1
  %latch.c = icmp ult i8 %0, 10
  %iv.next = add i32 %iv, 1
  br i1 %latch.c, label %loop.header, label %exit

exit:
  %t = icmp ult i32 %iv, 1236
  ret i1 %t
}

define i1 @multi_exiting_loop_eq_same_exit_with_out_loop_preds_const_compare_not_known(ptr %s, i1 %pre.c, i32 %x) {
; CHECK-LABEL: define i1 @multi_exiting_loop_eq_same_exit_with_out_loop_preds_const_compare_not_known(
; CHECK-SAME: ptr [[S:%.*]], i1 [[PRE_C:%.*]], i32 [[X:%.*]]) {
; CHECK-NEXT:  [[ENTRY:.*]]:
; CHECK-NEXT:    br i1 [[PRE_C]], label %[[LOOP_HEADER:.*]], label %[[EXIT:.*]]
; CHECK:       [[LOOP_HEADER]]:
; CHECK-NEXT:    [[IV:%.*]] = phi i32 [ 0, %[[ENTRY]] ], [ [[IV_NEXT:%.*]], %[[LOOP_LATCH:.*]] ]
; CHECK-NEXT:    [[EXITCOND_NOT:%.*]] = icmp eq i32 [[IV]], 1234
; CHECK-NEXT:    br i1 [[EXITCOND_NOT]], label %[[EXIT]], label %[[LOOP_LATCH]]
; CHECK:       [[LOOP_LATCH]]:
; CHECK-NEXT:    [[ARRAYIDX:%.*]] = getelementptr inbounds i8, ptr [[S]], i32 [[IV]]
; CHECK-NEXT:    [[TMP0:%.*]] = load i8, ptr [[ARRAYIDX]], align 1
; CHECK-NEXT:    [[LATCH_C:%.*]] = icmp ult i8 [[TMP0]], 10
; CHECK-NEXT:    [[IV_NEXT]] = add nuw nsw i32 [[IV]], 1
; CHECK-NEXT:    br i1 [[LATCH_C]], label %[[LOOP_HEADER]], label %[[EXIT]]
; CHECK:       [[EXIT]]:
; CHECK-NEXT:    [[P:%.*]] = phi i32 [ [[X]], %[[ENTRY]] ], [ [[IV]], %[[LOOP_HEADER]] ], [ [[IV]], %[[LOOP_LATCH]] ]
; CHECK-NEXT:    [[U:%.*]] = icmp ult i32 [[P]], 1235
; CHECK-NEXT:    ret i1 [[U]]
;
entry:
  br i1 %pre.c, label %loop.header, label %exit

loop.header:
  %iv = phi i32 [ 0, %entry ], [ %iv.next, %loop.latch ]
  %exitcond.not = icmp eq i32 %iv, 1234
  br i1 %exitcond.not, label %exit, label %loop.latch

loop.latch:
  %arrayidx = getelementptr inbounds i8, ptr %s, i32 %iv
  %0 = load i8, ptr %arrayidx, align 1
  %latch.c = icmp ult i8 %0, 10
  %iv.next = add nuw nsw i32 %iv, 1
  br i1 %latch.c, label %loop.header, label %exit

exit:
  %p = phi i32 [ %x, %entry ], [ %iv, %loop.header ], [ %iv, %loop.latch ]
  %u = icmp ult i32 %p, 1235
  ret i1 %u
}

define i1 @multi_exiting_loop_eq_same_unique_exit_successors_swapped(ptr %s) {
; CHECK-LABEL: define i1 @multi_exiting_loop_eq_same_unique_exit_successors_swapped(
; CHECK-SAME: ptr [[S:%.*]]) {
; CHECK-NEXT:  [[ENTRY:.*]]:
; CHECK-NEXT:    br label %[[LOOP_HEADER:.*]]
; CHECK:       [[LOOP_HEADER]]:
; CHECK-NEXT:    [[IV:%.*]] = phi i32 [ 0, %[[ENTRY]] ], [ [[IV_NEXT:%.*]], %[[LOOP_LATCH:.*]] ]
; CHECK-NEXT:    [[EXITCOND_NOT:%.*]] = icmp eq i32 [[IV]], 1234
; CHECK-NEXT:    br i1 [[EXITCOND_NOT]], label %[[LOOP_LATCH]], label %[[EXIT:.*]]
; CHECK:       [[LOOP_LATCH]]:
; CHECK-NEXT:    [[ARRAYIDX:%.*]] = getelementptr inbounds i8, ptr [[S]], i32 [[IV]]
; CHECK-NEXT:    [[TMP0:%.*]] = load i8, ptr [[ARRAYIDX]], align 1
; CHECK-NEXT:    [[LATCH_C:%.*]] = icmp ult i8 [[TMP0]], 10
; CHECK-NEXT:    [[IV_NEXT]] = add nuw nsw i32 [[IV]], 1
; CHECK-NEXT:    br i1 [[LATCH_C]], label %[[LOOP_HEADER]], label %[[EXIT]]
; CHECK:       [[EXIT]]:
; CHECK-NEXT:    [[U:%.*]] = icmp ult i32 [[IV]], 1235
; CHECK-NEXT:    ret i1 [[U]]
;
entry:
  br label %loop.header

loop.header:
  %iv = phi i32 [ 0, %entry ], [ %iv.next, %loop.latch ]
  %exitcond.not = icmp eq i32 %iv, 1234
  br i1 %exitcond.not, label %loop.latch, label %exit

loop.latch:
  %arrayidx = getelementptr inbounds i8, ptr %s, i32 %iv
  %0 = load i8, ptr %arrayidx, align 1
  %latch.c = icmp ult i8 %0, 10
  %iv.next = add nuw nsw i32 %iv, 1
  br i1 %latch.c, label %loop.header, label %exit

exit:
  %u = icmp ult i32 %iv, 1235
  ret i1 %u
}

define i1 @multi_exiting_loop_eq_same_unique_exit_const_compare_not_known(ptr %s) {
; CHECK-LABEL: define i1 @multi_exiting_loop_eq_same_unique_exit_const_compare_not_known(
; CHECK-SAME: ptr [[S:%.*]]) {
; CHECK-NEXT:  [[ENTRY:.*]]:
; CHECK-NEXT:    br label %[[LOOP_HEADER:.*]]
; CHECK:       [[LOOP_HEADER]]:
; CHECK-NEXT:    [[IV:%.*]] = phi i32 [ 0, %[[ENTRY]] ], [ [[IV_NEXT:%.*]], %[[LOOP_LATCH:.*]] ]
; CHECK-NEXT:    [[EXITCOND_NOT:%.*]] = icmp eq i32 [[IV]], 1234
; CHECK-NEXT:    br i1 [[EXITCOND_NOT]], label %[[EXIT:.*]], label %[[LOOP_LATCH]]
; CHECK:       [[LOOP_LATCH]]:
; CHECK-NEXT:    [[ARRAYIDX:%.*]] = getelementptr inbounds i8, ptr [[S]], i32 [[IV]]
; CHECK-NEXT:    [[TMP0:%.*]] = load i8, ptr [[ARRAYIDX]], align 1
; CHECK-NEXT:    [[LATCH_C:%.*]] = icmp ult i8 [[TMP0]], 10
; CHECK-NEXT:    [[IV_NEXT]] = add nuw nsw i32 [[IV]], 1
; CHECK-NEXT:    br i1 [[LATCH_C]], label %[[LOOP_HEADER]], label %[[EXIT]]
; CHECK:       [[EXIT]]:
; CHECK-NEXT:    [[U:%.*]] = icmp ult i32 [[IV]], 1234
; CHECK-NEXT:    ret i1 [[U]]
;
entry:
  br label %loop.header

loop.header:
  %iv = phi i32 [ 0, %entry ], [ %iv.next, %loop.latch ]
  %exitcond.not = icmp eq i32 %iv, 1234
  br i1 %exitcond.not, label %exit, label %loop.latch

loop.latch:
  %arrayidx = getelementptr inbounds i8, ptr %s, i32 %iv
  %0 = load i8, ptr %arrayidx, align 1
  %latch.c = icmp ult i8 %0, 10
  %iv.next = add nuw nsw i32 %iv, 1
  br i1 %latch.c, label %loop.header, label %exit

exit:
  %u = icmp ult i32 %iv, 1234
  ret i1 %u
}

define i1 @multi_exiting_loop_eq_same_unique_exit_var_compare_known(ptr %s, i32 %N) {
; CHECK-LABEL: define i1 @multi_exiting_loop_eq_same_unique_exit_var_compare_known(
; CHECK-SAME: ptr [[S:%.*]], i32 [[N:%.*]]) {
; CHECK-NEXT:  [[ENTRY:.*]]:
; CHECK-NEXT:    br label %[[LOOP_HEADER:.*]]
; CHECK:       [[LOOP_HEADER]]:
; CHECK-NEXT:    [[IV:%.*]] = phi i32 [ 0, %[[ENTRY]] ], [ [[IV_NEXT:%.*]], %[[LOOP_LATCH:.*]] ]
; CHECK-NEXT:    [[EXITCOND_NOT:%.*]] = icmp eq i32 [[IV]], [[N]]
; CHECK-NEXT:    br i1 [[EXITCOND_NOT]], label %[[EXIT:.*]], label %[[LOOP_LATCH]]
; CHECK:       [[LOOP_LATCH]]:
; CHECK-NEXT:    [[ARRAYIDX:%.*]] = getelementptr inbounds i8, ptr [[S]], i32 [[IV]]
; CHECK-NEXT:    [[TMP0:%.*]] = load i8, ptr [[ARRAYIDX]], align 1
; CHECK-NEXT:    [[LATCH_C:%.*]] = icmp ult i8 [[TMP0]], 10
; CHECK-NEXT:    [[IV_NEXT]] = add nuw nsw i32 [[IV]], 1
; CHECK-NEXT:    br i1 [[LATCH_C]], label %[[LOOP_HEADER]], label %[[EXIT]]
; CHECK:       [[EXIT]]:
; CHECK-NEXT:    [[T:%.*]] = icmp ule i32 [[IV]], [[N]]
; CHECK-NEXT:    ret i1 [[T]]
;
entry:
  br label %loop.header

loop.header:
  %iv = phi i32 [ 0, %entry ], [ %iv.next, %loop.latch ]
  %exitcond.not = icmp eq i32 %iv, %N
  br i1 %exitcond.not, label %exit, label %loop.latch

loop.latch:
  %arrayidx = getelementptr inbounds i8, ptr %s, i32 %iv
  %0 = load i8, ptr %arrayidx, align 1
  %latch.c = icmp ult i8 %0, 10
  %iv.next = add nuw nsw i32 %iv, 1
  br i1 %latch.c, label %loop.header, label %exit

exit:
  %t = icmp ule i32 %iv, %N
  ret i1 %t
}

define i1 @multi_exiting_loop_ne_same_unique_exit_const_compare_known(ptr %s) {
; CHECK-LABEL: define i1 @multi_exiting_loop_ne_same_unique_exit_const_compare_known(
; CHECK-SAME: ptr [[S:%.*]]) {
; CHECK-NEXT:  [[ENTRY:.*]]:
; CHECK-NEXT:    br label %[[LOOP_HEADER:.*]]
; CHECK:       [[LOOP_HEADER]]:
; CHECK-NEXT:    [[IV:%.*]] = phi i32 [ 0, %[[ENTRY]] ], [ [[IV_NEXT:%.*]], %[[LOOP_LATCH:.*]] ]
; CHECK-NEXT:    [[EXITCOND_NOT:%.*]] = icmp ne i32 [[IV]], 1234
; CHECK-NEXT:    br i1 [[EXITCOND_NOT]], label %[[LOOP_LATCH]], label %[[EXIT:.*]]
; CHECK:       [[LOOP_LATCH]]:
; CHECK-NEXT:    [[ARRAYIDX:%.*]] = getelementptr inbounds i8, ptr [[S]], i32 [[IV]]
; CHECK-NEXT:    [[TMP0:%.*]] = load i8, ptr [[ARRAYIDX]], align 1
; CHECK-NEXT:    [[LATCH_C:%.*]] = icmp ult i8 [[TMP0]], 10
; CHECK-NEXT:    [[IV_NEXT]] = add nuw nsw i32 [[IV]], 1
; CHECK-NEXT:    br i1 [[LATCH_C]], label %[[LOOP_HEADER]], label %[[EXIT]]
; CHECK:       [[EXIT]]:
; CHECK-NEXT:    [[T:%.*]] = icmp ult i32 [[IV]], 1235
; CHECK-NEXT:    ret i1 [[T]]
;
entry:
  br label %loop.header

loop.header:
  %iv = phi i32 [ 0, %entry ], [ %iv.next, %loop.latch ]
  %exitcond.not = icmp ne i32 %iv, 1234
  br i1 %exitcond.not, label %loop.latch, label %exit

loop.latch:
  %arrayidx = getelementptr inbounds i8, ptr %s, i32 %iv
  %0 = load i8, ptr %arrayidx, align 1
  %latch.c = icmp ult i8 %0, 10
  %iv.next = add nuw nsw i32 %iv, 1
  br i1 %latch.c, label %loop.header, label %exit

exit:
  %t = icmp ult i32 %iv, 1235
  ret i1 %t
}

define i1 @multi_exiting_loop_ne_same_unique_exit_successors_swapped(ptr %s) {
; CHECK-LABEL: define i1 @multi_exiting_loop_ne_same_unique_exit_successors_swapped(
; CHECK-SAME: ptr [[S:%.*]]) {
; CHECK-NEXT:  [[ENTRY:.*]]:
; CHECK-NEXT:    br label %[[LOOP_HEADER:.*]]
; CHECK:       [[LOOP_HEADER]]:
; CHECK-NEXT:    [[IV:%.*]] = phi i32 [ 0, %[[ENTRY]] ], [ [[IV_NEXT:%.*]], %[[LOOP_LATCH:.*]] ]
; CHECK-NEXT:    [[EXITCOND_NOT:%.*]] = icmp ne i32 [[IV]], 1234
; CHECK-NEXT:    br i1 [[EXITCOND_NOT]], label %[[EXIT:.*]], label %[[LOOP_LATCH]]
; CHECK:       [[LOOP_LATCH]]:
; CHECK-NEXT:    [[ARRAYIDX:%.*]] = getelementptr inbounds i8, ptr [[S]], i32 [[IV]]
; CHECK-NEXT:    [[TMP0:%.*]] = load i8, ptr [[ARRAYIDX]], align 1
; CHECK-NEXT:    [[LATCH_C:%.*]] = icmp ult i8 [[TMP0]], 10
; CHECK-NEXT:    [[IV_NEXT]] = add nuw nsw i32 [[IV]], 1
; CHECK-NEXT:    br i1 [[LATCH_C]], label %[[LOOP_HEADER]], label %[[EXIT]]
; CHECK:       [[EXIT]]:
; CHECK-NEXT:    [[U:%.*]] = icmp ult i32 [[IV]], 1235
; CHECK-NEXT:    ret i1 [[U]]
;
entry:
  br label %loop.header

loop.header:
  %iv = phi i32 [ 0, %entry ], [ %iv.next, %loop.latch ]
  %exitcond.not = icmp ne i32 %iv, 1234
  br i1 %exitcond.not, label %exit, label %loop.latch

loop.latch:
  %arrayidx = getelementptr inbounds i8, ptr %s, i32 %iv
  %0 = load i8, ptr %arrayidx, align 1
  %latch.c = icmp ult i8 %0, 10
  %iv.next = add nuw nsw i32 %iv, 1
  br i1 %latch.c, label %loop.header, label %exit

exit:
  %u = icmp ult i32 %iv, 1235
  ret i1 %u
}
