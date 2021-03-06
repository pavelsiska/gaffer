//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//      * Neither the name of John Haddon nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
//
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////

#include "Gaffer/Switch.inl"

#include "GafferScene/SceneSwitch.h"

using namespace GafferScene;

namespace
{

/// \todo If we introduce a TemporaryContext base class in Context.h
/// then this should derive from that. In fact, we might even define
/// this publicly as GafferScene::GlobalContext and then we could also
/// use it in ScenePlug::set() and other places we want to suppress the
/// scene path.
struct SceneSwitchIndexContext
{

	SceneSwitchIndexContext( const Gaffer::Context *context )
		:	m_context( new Gaffer::Context( *context, Gaffer::Context::Borrowed ) ),
			m_scopedContext( m_context.get() )
	{
		m_context->remove( ScenePlug::scenePathContextName );
		m_context->remove( Filter::inputSceneContextName );
	}

	private :

		Gaffer::ContextPtr m_context;
		Gaffer::Context::Scope m_scopedContext;

};

} // namespace

namespace Gaffer
{

IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( GafferScene::SceneSwitch, GafferScene::SceneSwitchTypeId )

template<>
struct SwitchTraits<GafferScene::SceneProcessor>
{

	typedef SceneSwitchIndexContext IndexContext;

};

} // namespace Gaffer

// explicit instantiation
template class Gaffer::Switch<GafferScene::SceneProcessor>;
