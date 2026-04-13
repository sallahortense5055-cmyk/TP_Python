from flask import Blueprint, request, jsonify, render_template
from extensions import db
from models import Electeur, Candidat, Vote, Election

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')


# ── Élections ──────────────────────────────────────────

@main.route('/elections', methods=['GET'])
def list_elections():
    elections = Election.query.all()
    return jsonify([
        {"id": e.id, "titre": e.titre, "ouverte": e.ouverte}
        for e in elections
    ])


@main.route('/elections', methods=['POST'])
def create_election():
    data = request.json
    if not data or not data.get('titre'):
        return jsonify({"erreur": "Le titre est obligatoire"}), 400
    election = Election(titre=data['titre'])
    db.session.add(election)
    db.session.commit()
    return jsonify({"id": election.id, "titre": election.titre}), 201


# ── Électeurs ──────────────────────────────────────────

@main.route('/electeurs', methods=['GET'])
def list_electeurs():
    electeurs = Electeur.query.all()
    return jsonify([
        {"id": e.id, "nom": e.nom, "email": e.email}
        for e in electeurs
    ])


@main.route('/electeurs', methods=['POST'])
def create_electeur():
    data = request.json
    if not data or not all(k in data for k in ('nom', 'email', 'mot_de_passe')):
        return jsonify({"erreur": "Champs manquants : nom, email, mot_de_passe"}), 400
    if Electeur.query.filter_by(email=data['email']).first():
        return jsonify({"erreur": "Email déjà utilisé"}), 400
    electeur = Electeur(nom=data['nom'], email=data['email'], mot_de_passe="")
    electeur.set_password(data['mot_de_passe'])
    db.session.add(electeur)
    db.session.commit()
    return jsonify({"id": electeur.id, "nom": electeur.nom}), 201


# ── Candidats ──────────────────────────────────────────

@main.route('/candidats', methods=['GET'])
def list_candidats():
    candidats = Candidat.query.all()
    return jsonify([
        {"id": c.id, "nom": c.nom, "election_id": c.election_id}
        for c in candidats
    ])


@main.route('/candidats', methods=['POST'])
def create_candidat():
    data = request.json
    if not data or not data.get('nom'):
        return jsonify({"erreur": "Le nom est obligatoire"}), 400
    candidat = Candidat(nom=data['nom'], election_id=data.get('election_id'))
    db.session.add(candidat)
    db.session.commit()
    return jsonify({"id": candidat.id, "nom": candidat.nom}), 201


# ── Vote ───────────────────────────────────────────────

@main.route('/vote', methods=['POST'])
def voter():
    data = request.json
    if not data or not all(k in data for k in ('electeur_id', 'candidat_id')):
        return jsonify({"erreur": "Champs manquants : electeur_id, candidat_id"}), 400

    electeur = db.session.get(Electeur, data['electeur_id'])
    if not electeur:
        return jsonify({"erreur": "Électeur introuvable"}), 404

    candidat = db.session.get(Candidat, data['candidat_id'])
    if not candidat:
        return jsonify({"erreur": "Candidat introuvable"}), 404

    if not candidat.election_id:
        return jsonify({"erreur": "Ce candidat n'est lié à aucune élection"}), 400

    if candidat.election and not candidat.election.ouverte:
        return jsonify({"erreur": "Cette élection est fermée"}), 403

    deja_vote = Vote.query.filter_by(
        electeur_id=electeur.id,
        election_id=candidat.election_id
    ).first()
    if deja_vote:
        return jsonify({"erreur": "Cet électeur a déjà voté dans cette élection"}), 400

    vote = Vote(
        electeur_id=electeur.id,
        candidat_id=candidat.id,
        election_id=candidat.election_id
    )
    db.session.add(vote)
    db.session.commit()
    return jsonify({"message": "Vote enregistré avec succès"}), 201


# ── Résultats ──────────────────────────────────────────

@main.route('/resultats', methods=['GET'])
def resultats():
    candidats = Candidat.query.all()
    data = []
    for c in candidats:
        votes = Vote.query.filter_by(candidat_id=c.id).all()
        electeurs = [v.electeur.nom for v in votes]
        data.append({
            "candidat": c.nom,
            "election_id": c.election_id,
            "votes": len(votes),
            "electeurs": electeurs
        })
    data.sort(key=lambda x: x['votes'], reverse=True)
    return jsonify(data)