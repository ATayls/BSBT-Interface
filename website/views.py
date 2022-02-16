from flask import (Blueprint, redirect, render_template, request, session,
                   url_for, current_app)
from website.extensions import db
from website.models import (User, Ranking, KnownRegion, UnknowRegion, Cluster, Region,
                            SkippedRanking, ComparisonProbability)
import random
import numpy as np
import uuid

blueprint = Blueprint('views', __name__)

@blueprint.route('/')
def intro():
    session.clear()
    return render_template('ethics_approval.html')


@blueprint.route('/rank')
@blueprint.route('/rank/<rid1>/<rid2>')
def rank(rid1=None, rid2=None):

    if 'user_region_bucket' not in session:
        kw = KnownRegion.query.filter_by(user_id=session['user_id']).all()

        session['user_region_bucket'] = [x.region_id for x in kw]

    if current_app.config["USE_PROBABILITIES"]:
        id_list = [r[0] for r in ComparisonProbability.query.values(ComparisonProbability.id)]
        probability_list = [r[0] for r in ComparisonProbability.query.values(ComparisonProbability.probability)]
        pairing_id = int(np.random.choice(id_list, p=probability_list))
        pair = ComparisonProbability.query.filter_by(id=pairing_id).first()
        # Redraw from sample if a region is unknown
        if pair.region1_id not in session['user_region_bucket']:
            return redirect(url_for('.rank'))
        if pair.region2_id not in session['user_region_bucket']:
            return redirect(url_for('.rank'))
        r1_id = pair.region1_id
        r2_id = pair.region2_id

    else:
        r1_id = random.choice(session['user_region_bucket'])
        sublist = session['user_region_bucket'].copy()
        sublist.remove(r1_id)
        r2_id = random.choice(sublist)

    r1 = Region.query.filter_by(id=r1_id).first()
    r2 = Region.query.filter_by(id=r2_id).first()

    return render_template('ranking_interface.html', r1=r1, r2=r2)


@blueprint.route('/register', methods=['GET', 'POST'])
def register_user():
    session.clear()
    if request.method == 'POST':

        # Defaults for blank form
        name = str(uuid.uuid1())
        age, gender, occ = 0, "na", "na"

        if 'name' in request.form:
            name = request.form['name'].replace("'", "")
        if 'age' in request.form:
            age = request.form['age']
        if 'gender' in request.form:
            gender = request.form['gender']
        if 'occ' in request.form:
            occ = request.form['occupation']

        user = User(name=name, age=age, gender=gender, occupation=occ)
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id

        return render_template('introduction.html')

    return render_template('ethics_approval.html')


@blueprint.route('/store')
@blueprint.route('/store/<poorest>/<richest>')
def store_ranking(poorest=None, richest=None):
    r = Ranking(user_id=session['user_id'], poorest=poorest, richest=richest)

    db.session.add(r)
    db.session.commit()

    return redirect(url_for('.rank'))


@blueprint.route('/skip/<r1>/<r2>')
def skip_ranking(r1=None, r2=None):
    s = SkippedRanking(user_id=session['user_id'], r1=r1, r2=r2)

    db.session.add(s)
    db.session.commit()

    return redirect(url_for('.rank'))


@blueprint.route('/previous')
def previous_ranking():
    r = Ranking.query.filter_by(user_id=session['user_id']).order_by(
        Ranking.date.desc()).first()

    r.rejudged = True

    db.session.add(r)
    db.session.commit()

    r1 = Region.query.filter_by(id=r.poorest).first()
    r2 = Region.query.filter_by(id=r.richest).first()

    return render_template('ranking_interface.html', r1=r1, r2=r2)


@blueprint.route('/unknown/<swid>')
def store_unknown_region(swid):
    u = UnknowRegion(user_id=session['user_id'], region_id=swid)

    ks = session['user_region_bucket']
    ks.remove(int(swid))
    session['user_region_bucket'] = ks

    db.session.add(u)
    db.session.commit()

    return redirect(url_for('.rank'))


@blueprint.route('/known/<rid>')
def store_known_region(rid):
    r = KnownRegion(user_id=session['user_id'], region_id=rid)

    db.session.add(r)
    db.session.commit()

    return redirect(url_for('.known_regions_selection'))


@blueprint.route('/logout')
def logout():
    print(session.keys())
    session.clear()
    print(session.keys())
    return redirect(url_for('.intro'))


@blueprint.route('/selection/clusters')
def known_clusters_selection():
    if current_app.config['ALL_CLUSTERS_KNOWN']:
        for r in Region.query.all():
            r = KnownRegion(user_id=session['user_id'], region_id=r.id)
            db.session.add(r)
            db.session.commit()
        return redirect(url_for('.rank'))

    if 'clusters' not in session:
        session['clusters'] = [
            x[0] for x in db.session.query(Cluster.id).distinct().all()
        ]

    if len(session['clusters']) == 0:
        session.pop('clusters', None)
        return redirect(url_for('.rank'))

    id = session['clusters'].pop()
    session['clusters'] = session['clusters']
    return render_template('cluster.html', id=id)


@blueprint.route('/selection/regions')
@blueprint.route('/selection/regions/<parent_cluster_id>')
def known_regions_selection(parent_cluster_id=None):
    if 'regions' not in session:
        regions = Region.query.filter_by(cluster_id=parent_cluster_id).all()
        session['regions'] = [x.id for x in regions]

    if len(session['regions']) == 0:
        session.pop('regions', None)
        return redirect(url_for('.known_clusters_selection'))

    id = session['regions'].pop()
    session['regions'] = session['regions']

    r = Region.query.filter_by(id=id).first()

    return render_template('region.html', region=r)
