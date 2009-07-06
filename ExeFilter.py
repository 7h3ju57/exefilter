#!/usr/bin/python
# -*- coding: latin-1 -*-
"""
ExeFilter - programme principal

ExeFilter permet de filtrer des fichiers, courriels ou pages web, afin de
supprimer tout code ex�cutable et tout contenu potentiellement dangereux en
termes de s�curit� informatique.

ExeFilter peut �tre employ� soit comme script (lanc� directement depuis la
ligne de commande), soit comme module (import� dans un autre script).

Lanc� comme script, ExeFilter d�pollue un ensemble de fichiers situ�s dans un
r�pertoire et place le r�sultat dans un r�pertoire destination.
La source et la destination peuvent �tre fournies en ligne de commande,
ou bien gr�ce � la fonction transfert() si ce module est import�.

Ce fichier fait partie du projet ExeFilter.
URL du projet: U{http://admisource.gouv.fr/projects/exefilter}

@organization: DGA/CELAR
@author: U{Philippe Lagadec<mailto:philippe.lagadec(a)laposte.net>}
@author: U{Arnaud Kerr�neur<mailto:arnaud.kerreneur(a)dga.defense.gouv.fr>}
@author: U{Tanguy Vinceleux<mailto:tanguy.vinceleux(a)dga.defense.gouv.fr>}

@contact: U{Philippe Lagadec<mailto:philippe.lagadec(a)laposte.net>}

@copyright: DGA/CELAR 2004-2007
@license: CeCILL (open-source compatible GPL) - cf. code source ou fichier LICENCE.txt joint

@version: 1.01

@status: beta
"""

#==============================================================================
__docformat__ = 'epytext en'

#__author__  = "Philippe Lagadec, Tanguy Vinceleux, Arnaud Kerr�neur (DGA/CELAR)"
__date__    = "2007-09-10"
__version__ = "1.01"

#------------------------------------------------------------------------------
# LICENCE pour le projet ExeFilter:

# Copyright DGA/CELAR 2004-2007
# Auteurs:
# - Philippe Lagadec (PL) - philippe.lagadec(a)laposte.net
# - Arnaud Kerr�neur (AK) - arnaud.kerreneur(a)dga.defense.gouv.fr
# - Tanguy Vinceleux (TV) - tanguy.vinceleux(a)dga.defense.gouv.fr
#
# Ce logiciel est r�gi par la licence CeCILL soumise au droit fran�ais et
# respectant les principes de diffusion des logiciels libres. Vous pouvez
# utiliser, modifier et/ou redistribuer ce programme sous les conditions
# de la licence CeCILL telle que diffus�e par le CEA, le CNRS et l'INRIA
# sur le site "http://www.cecill.info". Une copie de cette licence est jointe
# dans les fichiers Licence_CeCILL_V2-fr.html et Licence_CeCILL_V2-en.html.
#
# En contrepartie de l'accessibilit� au code source et des droits de copie,
# de modification et de redistribution accord�s par cette licence, il n'est
# offert aux utilisateurs qu'une garantie limit�e.  Pour les m�mes raisons,
# seule une responsabilit� restreinte p�se sur l'auteur du programme,  le
# titulaire des droits patrimoniaux et les conc�dants successifs.
#
# A cet �gard  l'attention de l'utilisateur est attir�e sur les risques
# associ�s au chargement,  � l'utilisation,  � la modification et/ou au
# d�veloppement et � la reproduction du logiciel par l'utilisateur �tant
# donn� sa sp�cificit� de logiciel libre, qui peut le rendre complexe �
# manipuler et qui le r�serve donc � des d�veloppeurs et des professionnels
# avertis poss�dant  des  connaissances  informatiques approfondies.  Les
# utilisateurs sont donc invit�s � charger  et  tester  l'ad�quation  du
# logiciel � leurs besoins dans des conditions permettant d'assurer la
# s�curit� de leurs syst�mes et ou de leurs donn�es et, plus g�n�ralement,
# � l'utiliser et l'exploiter dans les m�mes conditions de s�curit�.
#
# Le fait que vous puissiez acc�der � cet en-t�te signifie que vous avez
# pris connaissance de la licence CeCILL, et que vous en avez accept� les
# termes.

#------------------------------------------------------------------------------
# HISTORIQUE:
# 2004-10-24 v0.01 PL: - 1�re version (Sas de d�pollution)
# 2004-2006  PL,AK,TV: - Nombreuses �volutions
# 2007-06-20 v1.01 PL: - 1�re version libre, transformation en ExeFilter
# 2007-07-24       PL: - Appel � get_username pour ameliorer la portabilit�
# 2007-09-13       PL: - Am�lioration portabilit� constantes, imports
# 2007-10-08       PL: - Ajout option -e pour exporter la politique en HTML
#                      - Journal syslog desactive par defaut
# 2007-10-22       PL: - Ajout options antivirus
# 2008-02-29       PL: - correction banniere et rapport avec XF_VERSION/DATE
#------------------------------------------------------------------------------
# A FAIRE :
#------------------------------------------------------------------------------

#=== IMPORTS ==================================================================

# modules standards Python:
import os, sys, time, socket, optparse, tempfile, os.path

# modules sp�cifiques � Windows:
if sys.platform == 'win32':
    try:
        import win32api , win32security
    except:
        raise ImportError, "the pywin32 module is not installed: see http://sourceforge.net/projects/pywin32"

# import du module path.py pour simplifier la gestion des fichiers/repertoires:
try:
    from path import path
except:
    raise ImportError, "the path module is not installed: see http://www.jorendorff.com/articles/python/path/"

# modules d'ExeFilter:
from commun import *
import Politique
import Rapport
import Journal
import Conteneur_Repertoire
import Conteneur_Fichier
import Parametres
# numero de version global (provenant de __init__.py)
from __init__ import __version__ as XF_VERSION
from __init__ import __date__ as XF_DATE

#TODO: a supprimer
import commun     # (n�cessaire pour certaines variables globales)
import Conteneur  # pour importer la variable Conteneur.RACINE_TEMP


#=== CONSTANTES ===============================================================

REP_RAPPORT    = os.path.join("log", "rapports")+os.sep # log\rapports\
REP_LOG        = os.path.join("log", "journaux")+os.sep # log\journaux\
REP_TEMP       = "temp" + os.sep        # temp\
REP_ARCHIVE    = "archivage" + os.sep   # archivage\
TAILLE_TEMP    = 10000    # taille max r�pertoire temp, en Mo
TAILLE_ARCHIVE = 10000    # taille max archive, en Mo

#=== VARIABLES GLOBALES =======================================================

#TODO: a supprimer pour permettre plusieurs transferts simultan�s
nom_rapport       = None
nom_journal_secu  = None
transfert_termine = False

# Param�tres d'ExeFilter, avec leurs valeurs par d�faut:
parametres = {}

#--- REPERTOIRES ---
Parametres.Parametre("rep_rapports", str, nom="R�pertoire des fichiers rapports",
    description="R�pertoire o� sont stock�s tous les fichiers rapports",
    valeur_defaut = REP_RAPPORT).ajouter(parametres)
Parametres.Parametre("rep_journaux", str, nom="R�pertoire des fichiers journaux",
    description="R�pertoire o� sont stock�s tous les fichiers journaux",
    valeur_defaut = REP_LOG).ajouter(parametres)
Parametres.Parametre("rep_temp", str, nom="R�pertoire des fichiers temporaires",
    description="R�pertoire o� sont stock�s tous les fichiers temporaires",
    valeur_defaut = REP_TEMP).ajouter(parametres)
Parametres.Parametre("rep_archives", str, nom="R�pertoire des fichiers archiv�s",
    description="R�pertoire o� sont archiv�s tous les fichiers transf�r�s",
    valeur_defaut = REP_ARCHIVE).ajouter(parametres)
Parametres.Parametre("taille_temp", int, nom="Taille maximale du r�pertoire temporaire (en octets)",
    description="Taille maximale du r�pertoire o� sont stock�s tous les "
    +"fichiers temporaires",
    valeur_defaut = TAILLE_TEMP*1000000).ajouter(parametres)
Parametres.Parametre("taille_archives", int, nom="Taille maximale des archives (en octets)",
    description="Taille maximale du r�pertoire o� sont archiv�s tous les "
    +"fichiers transf�r�s",
    valeur_defaut = TAILLE_ARCHIVE*1000000).ajouter(parametres)

#--- JOURNAUX ---
Parametres.Parametre("journal_securite", bool, nom="Ecrire un journal s�curit� dans un fichier",
    description="Le journal s�curit� d�crit synth�tiquement les �v�nements "
    +"concernant la s�curit� des transferts.",
    valeur_defaut = True).ajouter(parametres)
Parametres.Parametre("journal_syslog", bool, nom="Envoyer un journal s�curit� par syslog",
    description="Le journal s�curit� d�crit synth�tiquement les �v�nements "
    +"concernant la s�curit� des transferts. Syslog permet de centraliser ces "
    +"journaux par le r�seau sur un serveur",
    valeur_defaut = False).ajouter(parametres)
Parametres.Parametre("journal_debug", bool, nom="Ecrire un journal technique de d�bogage",
    description="Le journal technique contient les �v�nements d�taill�s des "
    +"transferts, pour un d�bogage en cas de probl�me.",
    valeur_defaut = True).ajouter(parametres)
Parametres.Parametre("serveur_syslog", str, nom="Serveur syslog (nom ou adresse IP)",
    description="Nom ou adresse IP du serveur syslog qui centralise les journaux s�curit�.",
    valeur_defaut = "localhost").ajouter(parametres)
Parametres.Parametre("port_syslog", int, nom="Port syslog (num�ro de port UDP)",
    description="Num�ro de port UDP du serveur syslog: 514 pour un serveur syslog standard.",
    valeur_defaut = 514).ajouter(parametres)

#--- ANTIVIRUS ---

# ClamAV (clamd):
Parametres.Parametre("antivirus_clamd", bool, nom="Utiliser l'antivirus ClamAV (serveur clamd)",
    description="Utiliser la version serveur de l'antivirus ClamAV (clamd) "
               +"pour analyser les fichiers acceptes. Clamd doit tourner en "
               +"tant que service sur la machine locale.",
    valeur_defaut = False).ajouter(parametres)
Parametres.Parametre("clamd_serveur", str, nom="Adresse IP ou nom du serveur antivirus clamd",
    description="En general le serveur clamd tourne sur la meme machine: localhost.",
    valeur_defaut = 'localhost').ajouter(parametres)
Parametres.Parametre("clamd_port", int, nom="Port du serveur antivirus clamd",
    description="En general le serveur clamd tourne sur le port 3310.",
    valeur_defaut = 3310).ajouter(parametres)

# F-Prot 6.x (fpscan):
Parametres.Parametre("antivirus_fpscan", bool, nom="Utiliser l'antivirus F-Prot 6 (fpscan)",
    description="Utiliser la version ligne de commande de l'antivirus F-Prot 6 "
               +"(fpscan) pour analyser les fichiers acceptes. Attention cela "
               +"peut degrader significativement les performances.",
    valeur_defaut = False).ajouter(parametres)
if sys.platform == 'win32': fpscan_defaut = "c:\\Program Files\\FRISK Software\\F-PROT Antivirus for Windows\\fpscan.exe"
else:                       fpscan_defaut = "fpscan" # on suppose qu'il est dans le PATH
Parametres.Parametre("fpscan_executable", str, nom="Ex�cutable de l'antivirus F-Prot 6 (fpscan)",
    description="Emplacement du fichier fpscan de l'antivirus F-Prot 6",
    valeur_defaut = fpscan_defaut).ajouter(parametres)

# F-Prot 3.x (fpcmd, obsolete):
Parametres.Parametre("antivirus_fpcmd", bool, nom="Utiliser l'antivirus F-Prot 3 (fpcmd)",
    description="Utiliser la version ligne de commande de l'antivirus F-Prot 3 "
               +"(fpcmd) pour analyser les fichiers acceptes. Attention cela "
               +"peut degrader significativement les performances.",
    valeur_defaut = False).ajouter(parametres)
#TODO: verifier le chemin par defaut + am�liorer portabilit�
if sys.platform == 'win32': fpcmd_defaut = "c:\\Program Files\\FRISK Software\\F-PROT Antivirus for Windows\\fpcmd.exe"
else:                       fpcmd_defaut = "fpcmd" # on suppose que fpcmd est dans le PATH
Parametres.Parametre("fpcmd_executable", str, nom="Ex�cutable de l'antivirus F-Prot 3 (fpcmd)",
    description="Emplacement du fichier fpcmd de l'antivirus F-Prot 3",
    valeur_defaut = fpcmd_defaut).ajouter(parametres)



#=== FONCTIONS ================================================================

#------------------------------------------------------------------------------
# GET_JOURNAL
#-------------------
def get_journal() :
    """
    Retourne le chemin du fichier journal securite.
    Si le fichier journal n'est pas encore cr��, renvoie None

    @return: le chemin du fichier journal
    @rtype: str
    """
    if nom_journal_secu == None:
        #TODO: renvoyer une valeur par defaut ?
        return None
    else:
        rep_journaux = path(p.parametres['rep_journaux'].valeur)
        return (rep_journaux / nom_journal_secu).abspath()

#------------------------------------------------------------------------------
# GET_JOURNAL_DEBUG
#-------------------
def get_journal_debug() :
    """
    Retourne le chemin du fichier journal de d�bogage.
    Si le fichier journal n'est pas encore cr��, renvoie None

    @return: le chemin du fichier journal
    @rtype: str
    """
    if nom_journal_debug == None:
        #TODO: renvoyer une valeur par defaut ?
        return None
    else:
        rep_journaux = path(p.parametres['rep_journaux'].valeur)
        return (rep_journaux / nom_journal_debug).abspath()

#------------------------------------------------------------------------------
# GET_RAPPORT
#-------------------

def get_rapport() :
    """
    Retourne le chemin d'acc�s au fichier contenant le rapport au format html
    Si le fichier du rapport n'est pas encore cr��, renvoie None

    @return: chemin d'acc�s au fichier contenant le rapport au format html
    @rtype: str
    """
    if nom_rapport == None:
        chemin_rapport = None
    else:
        #chemin_rapport = REP_RAPPORT + nom_rapport
        chemin_rapport = path(p.parametres['rep_rapports'].valeur) / nom_rapport
        chemin_rapport = chemin_rapport.abspath()
    return chemin_rapport

#------------------------------------------------------------------------------
# CANCEL_TRANSFERT
#-------------------

def cancel_transfert ():
    """
    Annule le transfert en cours
    """
    commun.continuer_transfert = False

#------------------------------------------------------------------------------
# GET_NB_FICHIERS
#-------------------

def get_nb_fichiers ():
    """
    Retourne le nombre de fichiers � analyser ou None si le moteur
    n'a pas encore commenc� le transfert

    @return: le nombre de fichiers � analyser
    @rtype: int
    """
    if commun.transfert_commence == True : return commun.nb_fichiers
    else : return None

#------------------------------------------------------------------------------
# GET_COMPTEUR_AVANCEMENT
#-------------------------

def get_compteur_avancement ():
    """
    Retourne le nombre fichiers d�j� analyser ou None si le moteur
    n'a pas encore commenc� le transfert

    @return: le nombre de fichiers d�j� analys�s
    @rtype: int
    """
    if commun.transfert_commence == True : return commun.compteur_avancement
    else : return None

#------------------------------------------------------------------------------
# TRANSFERT
#-------------------

#def transfert(liste_source, destination, type_transfert="entree", handle=None,
#              taille_temp = TAILLE_ARCHIVE*1000000, pol=None):
def transfert(liste_source, destination, type_transfert="entree", handle=None,
              pol=None):
    """
    Lance le transfert et l'analyse des r�pertoires et/ou fichiers source

    @param liste_source: la liste des sources � transf�rer
    @type  liste_source: list

    @param destination: le r�pertoire destination
    @type  destination: str

    @param type_transfert: le type de transfert pour charger la politique de filtre
    @type  type_transfert: str

    @param handle: le handle de connexion a utiliser pour ex�cuter le filtre
    @type  handle: pyHandle

    #@param taille_temp: taille maximale du r�pertoire temporaire, en octets. Taille par d�faut 10Go (DVD double couche)
    #@type  taille_temp: int
    """

    global nom_journal_secu
    global nom_journal_debug
    global nom_rapport
    global p

    if sys.platform == 'win32':
        if handle != None :
            win32security.ImpersonateLoggedOnUser(handle)

    taille_src = 0

    # cr�ation du tronc commun pour les noms des journaux et des rapports:
    nom_machine = socket.gethostname()
    date = time.strftime("%Y-%m-%d", time.localtime())
    heure = time.strftime("%Hh%Mm%Ss", time.localtime())
    nom_commun = date + "_" + nom_machine + "_" + get_username() + "_" + heure

    # nom des fichiers log = nom de la machine + date et heure du transfert
    nom_journal_secu = "Journal_secu_" + nom_commun + ".log"
    nom_journal_debug = "Journal_debug_" + nom_commun + ".log"

#    on transmet � transfert :
#            soit un objet Politique d�j� configur�,
#            soit un nom de fichier de config directement,
#            soit une liste de fichiers de config,
#            soit un mot-cl� " entree " ou " sortie " d�crivant le type de transfert,
#            afin de conserver la compatibilit� avec l'IHM actuelle. Dans ce cas le fichier de config filtres.cfg doit �tre analys� correctement.
    if pol != None:
        if isinstance(pol, Politique.Politique):
            p = pol
        elif isinstance (pol,  [file, str, unicode, list]):
            p = Politique.Politique(pol)
    elif type_transfert in ("entree", "sortie"):
            # v�rifier si le fichier existe
            # si le fichier existe alors on le charge
            # sinon politque par d�faut
            # p = Politique.Politique("politique_%s.cfg" % type_transfert)
            p = Politique.Politique()
    else:
        # politique par d�faut
        p = Politique.Politique()

    commun.politique = p

    # cr�ation du journal d'�v�nements:
    Journal.init_journal(p, journal_secu = get_journal(), journal_debug = get_journal_debug())

    # cr�ation des sous-r�pertoires temp et archivage:
    commun.sous_rep_archive = commun.sous_rep_temp = "transfert_" + nom_commun

    # on r�cup�re le nom de l'utilisateur qui lance ExeFilter, avec nom de
    # domaine (ou de machine) sous Windows:
    user = get_username(with_domain=True)

    Journal.important(u"ExeFilter v%s lanc� par utilisateur %s sur la machine %s" %
        (XF_VERSION, user, nom_machine))

    # on ajoute la politique dans le journal:
    p.journaliser()
    Journal.info2(u"D�but de l'analyse")

    Rapport.liste_resultats = []

    # liste des r�pertoires et/ou fichiers source
    liste_conteneurs_source = []

    # initialisation des variables globales
    commun.nb_fichiers = commun.compteur_avancement = 0
    commun.continuer_transfert = True
    commun.transfert_commence = False

    # boucle pour lire chaque r�pertoire et/ou fichier contenu dans    la liste
    for source in liste_source :
        # on v�rifie le type de source: r�pertoire ou fichier ?
        if os.path.isdir(source):
            #rep_source = Conteneur_Repertoire.Conteneur_Repertoire (source, destination)

            # si source est G:/tutu/tata, rep_relatif_source = tata
            (head, tail) = os.path.split(source)
            rep_relatif_source = tail
            rep_source = Conteneur_Repertoire.Conteneur_Repertoire (source, destination, rep_relatif_source)

            # calcul de la taille du r�pertoire source
            taille_src += rep_source.compter_taille_rep()

        else:
            #rep_source = Conteneur_Fichier.Conteneur_Fichier (source, destination)

            rep_relatif_source = ""
            rep_source = Conteneur_Fichier.Conteneur_Fichier (source, destination, rep_relatif_source)

            # calcul de la taille du fichier source
            taille_src += os.stat(source).st_size

        # on ajoute les conteneurs source � la liste
        liste_conteneurs_source.append(rep_source)
        # on incr�mente le compteur nombre de fichiers total
        commun.nb_fichiers += rep_source.compter_nb_fichiers()

    # calcul de ta taille du r�pertoire archivage
    taille_rep = 0
    chem_src = path(commun.politique.parametres['rep_archives'].valeur)
    for rep in chem_src.walkfiles():
        taille_rep += os.stat(rep).st_size

    # test si la taille des fichiers source est sup�rieure � celle du r�p temp
    # si c'est le cas, on g�n�re une exception
    #if taille_src > taille_temp:
    if taille_src >    p.parametres['taille_temp'].valeur:
        msg = "La taille des fichiers source est superieure a la taille du repertoire temporaire."
        Journal.error(msg)
        raise RuntimeError, msg

    # test si la taille des fichiers source est sup�rieure � celle du r�p d'archivage
    # si c'est le cas, on g�n�re une exception
    if taille_src >    p.parametres['taille_archives'].valeur:
        msg = "La taille des fichiers source est superieure a la taille du repertoire d'archivage."
        Journal.error(msg)
        raise RuntimeError, msg

    # boucle pour effacer les sous-r�p les plus anciens dans le cas o� il n'y a pas assez
    # d'espace disque dans le r�p archivage pour copier les fichiers source
    while p.parametres['taille_archives'].valeur < taille_rep + taille_src:
        date_archive = 0
        taille_rep_archive = 0
        # boucle pour d�terminer quel est le sous-r�p archive le plus ancien
        for rep in chem_src.dirs():
            if date_archive == 0:
                # on r�cup�re la date du 1er sous-r�p archive lu
                date_archive = os.path.getmtime(rep)
                rep_archive = rep
            # si la date du sous-r�p archive lu est inf�rieure � date_archive,
            # ce sous-r�p devient le plus ancien
            elif date_archive > os.path.getmtime(rep):
                date_archive = os.path.getmtime(rep)
                rep_archive = rep
        if os.path.exists(rep_archive):
            # calcul de la taille du sous-r�p archive le plus ancien
            for rep in rep_archive.walkfiles():
                taille_rep_archive += os.stat(rep).st_size
            # on met � jour la taille du r�p temp principal
            taille_rep = taille_rep - taille_rep_archive
            # on efface le sous-r�p temp le plus ancien
            rep_archive.rmtree()
        else:
            # s'il n'y a plus de sous-r�p archive � effacer, on g�n�re une exception
            msg = "repertoire d'archivage deja vide => taille source trop grande"
            Journal.error(msg)
            raise RuntimeError, msg

    commun.transfert_commence = True

    # boucle d'analyse de chaque conteneur source contenu dans la liste
    for conteneur_source in liste_conteneurs_source:
        Journal.info2(u"Analyse de contenu de %s ..." % conteneur_source)

        # ici il faudrait un try pour g�rer toutes les exceptions, journaliser
        # et nettoyer s'il y a des erreurs.
        # ou alors lancer un thread...

        # test de l'interruption de transfert par l'utilisateur
        if commun.continuer_transfert == True:
            # s'il n'y a pas d'interruption, on lance le nettoyage
            liste_resultat = conteneur_source.nettoyer(p)
        # s'il y a eu une interruption pendant nettoyer(), on s'arr�te
        if commun.continuer_transfert == False:break

    # g�n�ration du rapport
    nom_rapport = "rapport_" + nom_commun
    Journal.info2(u"G�n�ration du rapport: %s ..." % nom_rapport)
    resume = Rapport.generer_rapport(p.parametres['rep_rapports'].valeur + nom_rapport,
                                      ', '.join(liste_source),  destination ,
                                      XF_VERSION,  XF_DATE, commun.continuer_transfert)
    Journal.info2(u"Fin de l'analyse")
    # log du r�sum� de la d�pollution
    Journal.important(u'R�sum� : %d fichiers analys�s ; '\
        u'%d fichiers accept�s ; %d fichiers nettoy�s ; %d fichiers refus�s ; %d erreurs' \
        % (resume[0], resume[1], resume[2], resume[3], resume[4]))

    if commun.continuer_transfert == False:
        Journal.warning(u"TRANSFERT ANNULE par l'utilisateur")

    Journal.fermer_journal()
    return



#==============================================================================
# PROGRAMME PRINCIPAL
#=====================
# ne sert que si on appelle le module ExeFilter.py directement, sans passer par
# le module go.py qui lance la m�thode transfert du module ExeFilter.py dans un 
# thread.

if __name__ == '__main__':
    # si compilation py2exe, il faut fixer ici le codec par d�faut, car il n'y
    # a pas de sitecustomize.py:
    if hasattr(sys,"setdefaultencoding"):
            sys.setdefaultencoding("latin-1")

    print "-"*79
    print "ExeFilter v" + XF_VERSION + " du " + XF_DATE
    print "-"*79
    print ""

    # on cr�e un objet optparse.OptionParser pour analyser la ligne de commande:
    op = optparse.OptionParser(usage =
        "%prog [options] <fichiers ou repertoires a nettoyer>")

    op.add_option("-c", "--config", dest="config", default="",
        help="Fichier de configuration general pour ExeFilter")
    op.add_option("-p", "--politique", dest="politique", default="",
        help="Fichier de configuration pour la politique de filtrage")
    op.add_option("-d", "--dest", dest="destination", default="",
        help="Repertoire destination pour les fichiers nettoyes (obligatoire)")
    op.add_option("-v", "--verbose", action="store_true", dest="debug",
        default=False, help="Mode Debug (pour le developpement)")
    op.add_option("-n", "--nouvelle", dest="nouv_politique", default='',
        help="Creer une nouvelle politique dans un fichier INI/CFG")
    op.add_option("-e", "--export", dest="export_html", default='',
        help="Exporter la politique dans un fichier HTML")

    # on parse les options de ligne de commande:
    (options, args) = op.parse_args(sys.argv[1:])

    # si aucun fichier/r�pertoire � nettoyer, et si la destination n'est pas
    # sp�cifi�e, on force l'affichage de l'aide:
    if (len(args)==0 or options.destination == "") and options.export_html==''\
        and options.nouv_politique=='':
        op.print_help()
        print ""
        print "Il faut indiquer les fichiers/repertoires a nettoyer, ainsi qu'une destination."
        sys.exit(1)

    # on exploite les �ventuelles options
    if options.debug:
        mode_debug(True)

    # On cr�e d'abord une politique par d�faut:
    pol = Politique.Politique()
    # ensuite on charge le fichier de config g�n�ral si pr�cis�:
    if options.config:
        pol.lire_config(options.config)
    # puis le fichier de la politique:
    if options.politique:
        pol.lire_config(options.politique)

    # si l'option nouvelle politique est active on sauve la politique dans un
    # fichier INI:
    if options.nouv_politique != '':
        pol.ecrire_fichier(options.nouv_politique)
        print 'Politique sauvee dans le fichier %s' % options.nouv_politique
        sys.exit()

    # si l'option export est active on exporte la politique dans un fichier HTML:
    if options.export_html != '':
        pol.ecrire_html(options.export_html)
        print 'Politique exportee dans le fichier %s' % options.export_html
        sys.exit()

    # enfin on lance le transfert:
    # (les r�pertoires et/ou fichiers source sont dans la liste args)
    transfert(args, options.destination, pol=pol)



# POUBELLE: code � utiliser plus tard ou � supprimer:

#/    op.add_option("-a", "--archive", dest="archive",
#/        default=parametres["rep_archives"].valeur_defaut,
#/        help="Repertoire d'archivage des fichiers nettoyes [%default]")
#/    op.add_option("-j", "--journaux", dest="journaux",
#/        default=parametres["rep_journaux"].valeur_defaut,
#/        help="Repertoire de stockage des journaux [%default]")
#/    op.add_option("-r", "--rapports", dest="rapports",
#/        default=parametres["rep_rapports"].valeur_defaut,
#/        help="Repertoire de stockage des rapports [%default]")
#/    op.add_option("-t", "--temp", dest="temp",
#/        default=parametres["rep_temp"].valeur_defaut,
#/        help="Repertoire pour les fichiers temporaires [%default]")
#/    op.add_option("-s", "--syslog", dest="syslog",
#/        default=parametres["serveur_syslog"].valeur_defaut+":"
#/        + str(parametres["port_syslog"].valeur_defaut), metavar="SERVEUR:PORT",
#/        help="Adresse IP ou nom du serveur syslog, et port UDP [%default]")