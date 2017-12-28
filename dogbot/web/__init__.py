from flask import Flask, render_template, request, redirect, url_for
from dogbot.models import Class, Unit


app = Flask(__name__)


def model_list_expender(list, model):
    return [model.objects(id=material).first() for material in list if material]


@app.route('/')
def index():
    return redirect(url_for('units'))


@app.route('/class', methods=['GET', 'POST'])
def classes():
    if request.method == 'POST':
        if not request.form.get('id'):
            class_ = Class(
                name=request.form.get('name'),
                nickname=request.form.getlist('nickname'),
                translate=request.form.get('translate'),
                cc_material=model_list_expender(request.form.getlist('CCMaterial'), Class),
                awake_material=model_list_expender(request.form.getlist('awakeMaterial'), Class),
                awake_orb=model_list_expender(request.form.getlist('awakeOrb'), Class)
            )
        elif request.form.get('action'):
            # 删除
            class_ = Class.objects(id=request.form.get('id')).first()
            class_.delete()
            return 'ok', 200
        else:
            class_ = Class.objects(id=request.form.get('id')).first()
            class_.name = request.form.get('name')
            class_.nickname = request.form.getlist('nickname')
            class_.translate = request.form.get('translate')
            class_.cc_material = model_list_expender(request.form.getlist('CCMaterial'), Class)
            class_.awake_material = model_list_expender(request.form.getlist('awakeMaterial'), Class)
            class_.awake_orb = model_list_expender(request.form.getlist('awakeOrb'), Class)
        class_.save()
        return redirect(url_for('classes'))
    classes = Class.objects()
    return render_template('class.html', classes=classes)


@app.route('/unit', methods=['GET', 'POST'])
def units():
    if request.method == 'POST':
        if not request.form.get('id'):
            unit = Unit(
                name=request.form.get('name'),
                rarity=request.form.get('rarity') or None,
                class_=Class.objects(id=request.form.get('class')).first() if request.form.get('class') else None,
                nickname=request.form.getlist('nickname'),
                conne_name=request.form.get('conneName')
            )
        elif request.form.get('action'):
            # 删除
            unit = Unit.objects(id=request.form.get('id')).first()
            unit.delete()
            return 'ok', 200
        else:
            unit = Unit.objects(id=request.form.get('id')).first()
            unit.name = request.form.get('name')
            unit.rarity = request.form.get('rarity')
            unit.class_ = Class.objects(id=request.form.get('class')).first() if request.form.get('class') else None
            unit.nickname = request.form.getlist('nickname')
            unit.conne_name = request.form.get('conneName')
        unit.save()
        return redirect(url_for('units'))
    units = Unit.objects()
    classes = Class.objects()
    return render_template('unit.html', units=units, classes=classes)
