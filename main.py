"""
Point d'entrée principal pour le jeu Galad Islands.

Ce fichier coordonne l'initialisation et l'exécution du moteur
avec tous ses composants développés de façon modulaire.

Architecture: Composants autonomes + interfaces + event bus
"""

import sys
from pathlib import Path

# Ajouter le dossier src au path pour les imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Import du moteur principal (composant core)
from components.core.engine import GaladEngine, EtatJeu

# TODO: Les imports suivants seront décommentés au fur et à mesure
# que les composants sont développés

# from components.entities.entity_manager import EntityManager
# from components.renderer.game_renderer import GameRenderer
# from components.ai.ai_manager import AIManager
# from components.physics.physics_engine import PhysicsEngine
# from components.world.world_generator import WorldGenerator


def initialiser_composants_disponibles(moteur: GaladEngine) -> bool:
    """
    Initialise tous les composants disponibles.
    
    Cette fonction sera mise à jour au fur et à mesure que
    les composants sont développés.
    
    Args:
        moteur: Instance du moteur principal
        
    Returns:
        True si l'initialisation réussit
    """
    composants_initialises = 0
    
    print("🔧 Initialisation des composants disponibles...")
    
    # ===== COMPOSANT ENTITIES =====
    try:
        # from components.entities.entity_manager import EntityManager
        # entity_manager = EntityManager()
        # moteur.enregistrer_composant("entities", entity_manager)
        # composants_initialises += 1
        print("⏳ Composant entities: En développement")
    except ImportError:
        print("⏳ Composant entities: Pas encore disponible")
    except Exception as e:
        print(f"❌ Erreur composant entities: {e}")
        return False
    
    # ===== COMPOSANT RENDERER =====
    try:
        # from components.renderer.game_renderer import GameRenderer
        # renderer = GameRenderer(moteur.largeur, moteur.hauteur)
        # moteur.enregistrer_composant("renderer", renderer)
        # composants_initialises += 1
        print("⏳ Composant renderer: En développement")
    except ImportError:
        print("⏳ Composant renderer: Pas encore disponible")
    except Exception as e:
        print(f"❌ Erreur composant renderer: {e}")
        return False
    
    # ===== COMPOSANT AI =====
    try:
        # from components.ai.ai_manager import AIManager
        # ai_manager = AIManager()
        # moteur.enregistrer_composant("ai", ai_manager)
        # composants_initialises += 1
        print("⏳ Composant AI: En développement")
    except ImportError:
        print("⏳ Composant AI: Pas encore disponible")
    except Exception as e:
        print(f"❌ Erreur composant AI: {e}")
        return False
    
    # ===== COMPOSANT PHYSICS =====
    try:
        # from components.physics.physics_engine import PhysicsEngine
        # physics_engine = PhysicsEngine()
        # moteur.enregistrer_composant("physics", physics_engine)
        # composants_initialises += 1
        print("⏳ Composant physics: En développement")
    except ImportError:
        print("⏳ Composant physics: Pas encore disponible")
    except Exception as e:
        print(f"❌ Erreur composant physics: {e}")
        return False
    
    # ===== COMPOSANT WORLD =====
    try:
        # from components.world.world_generator import WorldGenerator
        # world_gen = WorldGenerator()
        # moteur.enregistrer_composant("world", world_gen)
        # composants_initialises += 1
        print("⏳ Composant world: En développement")
    except ImportError:
        print("⏳ Composant world: Pas encore disponible")
    except Exception as e:
        print(f"❌ Erreur composant world: {e}")
        return False
    
    print(f"✅ {composants_initialises}/5 composants initialisés")
    print("💡 Le moteur fonctionne avec les composants de fallback intégrés")
    
    return True


def afficher_status_composants():
    """Affiche le statut de développement de chaque composant."""
    print("\n" + "="*50)
    print("🏗️  STATUS DÉVELOPPEMENT GALAD ISLANDS")
    print("="*50)
    
    composants = [
        ("Core Engine", "✅ Moteur principal implémenté"),
        ("Entity System", "⏳ En développement"),
        ("Renderer", "⏳ En développement"),
        ("AI Manager", "⏳ En développement"),
        ("Physics Engine", "⏳ En développement"),
        ("World Generator", "⏳ En développement")
    ]
    
    for composant, status in composants:
        print(f"� {composant:15} | {status}")
    
    print("\n💡 Instructions:")
    print("   1. Développer chaque composant dans src/components/[nom]/")
    print("   2. Implémenter les interfaces définies dans src/interfaces/")
    print("   3. Utiliser l'event bus pour communiquer entre composants")
    print("   4. Tester le composant avec python dev.py --test-component [nom]")
    print("   5. Une fois prêt, décommenter l'import dans main.py")
    print("="*50)


def main():
    """Point d'entrée principal du jeu."""
    print("🎮 GALAD ISLANDS - Démarrage")
    print("Architecture: Moteur par composants")
    
    # Afficher le status des composants
    afficher_status_composants()
    
    # Créer le moteur principal
    try:
        moteur = GaladEngine(
            largeur=1280,
            hauteur=720,
            fps_cible=60
        )
        
        # Initialiser les composants disponibles
        if not initialiser_composants_disponibles(moteur):
            print("❌ Échec de l'initialisation des composants")
            return
        
        # Démarrer le jeu
        print("\n🚀 Démarrage du jeu...")
        moteur.demarrer()
        
    except KeyboardInterrupt:
        print("\n🔒 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()