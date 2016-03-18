//单项数量变化
$(function () {
    $('.jian,.jia').click(function () {
        var select_item = 0;
        var that = $(this);
        var target_class = that.attr("class").split(" ")[1];
        var val;
        var tr = that.parents(".item");
        var price = parseInt($("#j_zongjia").text());

        var unit_price = parseInt(tr.find(".price").text());
        if (target_class == 'jian') {
            val = $(this).next().val();
            if (val <= 1) {
                val = 0;
                that.find(".j_jian").attr("disabled", "disabled");
            } else {
                val--;
            }
            that.next().val(val);
            if (price - unit_price > 0) {
                price -= unit_price;
            }

        }
        else {
            tr.find(".j_jian").removeAttr("disabled");
            val = $(this).prev().val();
            val++;
            that.parent().children('#j_shuliang').val(val);

            price += unit_price;

        }
        $(".long_table").find(".item").each(function () {
            var quanity = parseInt($(this).find("#j_shuliang").val());
            if (quanity != 0) {
                select_item += 1
            }
        })

        //小计
        tr.find("#j_danjia").text(unit_price * val);
        // 更新选中商品数,商品总价
        $("#j_zongshu").text(select_item);
        $("#j_zongjia").text(price);
    });

    $("#goumaigo").click(function () {
        var data = [];
        var select_item = 0;
        $(".long_table").find(".item").each(function () {
            var id = $(this).data("id");

            var count = parseInt($(this).find("#j_shuliang").val());
            if (count != 0 && count) {
                select_item += 1;
                data.push({
                    'id': id,
                    'count': count
                })
            }

        })
        if (select_item == 0) {
            alert ("请至少选择一个商品再提交")
            return false
        }
        data = (JSON.stringify(data));
        $("#items").val(data);
        $("form").submit();

    })

});